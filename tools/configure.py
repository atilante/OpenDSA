#! /usr/bin/python
#
# This script builds an OpenDSA textbook according to a specified configuration file
#   - Runs config_validator.py on the specified config file to detect and inform the user of any errors
#   - Reads the configuration information from the specified JSON config file
#   - Auto-detects the OpenDSA root directory location
#   - Sets sensible defaults for optional configuration settings
#   - Converts the OpenDSA root directory and specified code and output directories into Unix-style paths so that relative paths are calculated correctly
#     - Handles absolute or relative paths for output and code directories (relative paths are rooted at the OpenDSA directory)
#   - Optionally builds JSAV to make sure the library is up-to-date, if specified in the configuration file
#   - Creates a source directory in the output directory and generates a Makefile and conf.py file
#     - Makefile is configured to copy the original .htaccess file from lib to the html output directory
#     - conf.py is configured to point to the original ODSAextensions and _themes directories
#     - CONTROLLING INCLUSION OF GLOBAL JS AND CSS FILES - conf.py contains a dictionary called html_context
#       which controls what JS and CSS files are included on ALL module pages, please see the assoicated comment
#       for more information
#   - Reads the RST source file for each module which appears in the configuration file
#     - Appends the list of external JavaScript and CSS links and a Sphinx self reference directive to every module
#       - Ensures we can reference any module, without relying on the module author to correctly add the reference link
#     - Optionally, appends a raw JavaScript flag to each module indicating whether or not the module can be completed
#       This allows the configuration file to override the default behavior of the client-side framework which is to allow
#       module completion only if the module contains required exercises
#     - For each figure encountered in the RST file, adds the name to a list so that we only copy the images used in the book
#       to the output directory
#     - For each inlineav directive encountered, configure.py attempts to append additional information from the configuration file
#       - If the specified exercise does not appear in the configuration file, the Sphinx directive will be included, but no
#         additional information will be included so the defaults (specified in the Sphinx directive file) will be used.  The
#         name of the exercise is added to a list of missing exercises which will be displayed to the user
#       - Specifically adds 'long_name', 'points', 'required' and 'threshold'
#     - For each avembed directive encountered, configure.py attempts to append additional information from the configuration file
#       - UNLESS the 'remove' attribute is present and "true", in which case the entire avembed directive is removed
#       - If the specified exercise does not appear in the configuration file, the Sphinx directive will be included, but no
#         additional information will be included so the defaults (specified in the Sphinx directive file) will be used.  The
#         name of the exercise is added to a list of missing exercises which will be displayed to the user
#       - Specifically adds 'long_name', 'points', 'required', 'showhide' and 'threshold'
#     - The configured module RST file is written to the source directory in the output file
#   - Generates an index.rst file based on which modules were specified in the config file
#   - Prints out a list of any exercises encountered in RST source files that did not appear in the config file
#   - Copies _static directory and the images contained in the list of encountered images to the output source directory, also
#     creates a copy of the config file in the _static directory for use by the gradebook page
#   - Generates _static/config.js which contains settings needed by the client-side framework that can be configured
#     using the config file
#   - Generates an index.html file in the output directory of the new book which redirects (via JavaScript) to the html/ directory
#   - Optionally runs make on the output directory to build the textbook, if specified in the configuration file

import sys
import os
import shutil
import distutils.dir_util
import distutils.file_util
import json
import collections
import re
import subprocess
import datetime
from optparse import OptionParser
from config_templates import *
from ODSA_RST_Module import ODSA_RST_Module
from ODSA_Config import ODSA_Config
from postprocessor import update_TOC

# List of exercises encountered in RST files that do not appear in the configuration file
missing_exercises = []

# List of modules that have been processed, do not allow multiple modules with the same name (would cause a conflict in the database)
processed_modules = []

# List of images encountered while processing module files, these will be copied from the source/Images to Images in the output source directory
images = []

# Stores information about ToDo directives
todo_list = []

# List of fulfilled prerequisite topics
satisfied_requirements = []

# Maps the chapter name and number to each module, used for correcting the numbers during postprocessing
module_chap_map = {}

# Dictionary which stores a mapping of sections to modules, modules to their numbers, and figures, tables, theorems, and equations to their numbers
num_ref_map = {}

# Processes a chapter or section of the book
#   - config - a dictionary containing all the configuration options
#   - section - a dictionary where all the keys are sections or modules
#   - index_rst - the index.rst file being generated
#   - depth - the depth of the recursion; 0 for the main chapters, 1 for any subsections, ..., N for the modules
#   - current_section_numbers - a list that contains the numbering scheme for each section or module ([chapter].[section].[...].[module])
#   - section_name - a string passed to modules for inclusion in the RST header that specifies which chapter / section the module belongs to
def process_section(config, section, index_rst, depth, current_section_numbers = [], section_name=''):
  # Initialize the section number for the current depth
  if depth >= len(current_section_numbers):
    current_section_numbers.append(config.start_chap_num)

  for subsect in section:
    # Parse the subsection name by eliminating the path and file extension if its a module
    subsect_name = os.path.splitext(os.path.basename(subsect))[0]
    num_ref_map[subsect_name] = -1 # Add the section name to num_ref_map

    if 'exercises' in section[subsect]:
      process_module(config, index_rst, subsect, section[subsect], depth, current_section_numbers, section_name)
    else:
      # List of characters Sphinx uses for headers, the depth of a section header determines which character to use
      sphinx_header_chars = ['=', '-', '`', "'", '.', '*', '+', '^']

      print ("  " * depth) + subsect
      index_rst.write(subsect + '\n')
      index_rst.write((sphinx_header_chars[depth] * len(subsect)) + "\n\n")
      index_rst.write(".. toctree::\n")
      index_rst.write("   :numbered:\n")
      index_rst.write("   :maxdepth: 3\n\n")
      process_section(config, section[subsect], index_rst, depth + 1, current_section_numbers, subsect_name)

    # Increments the section count at the current depth
    current_section_numbers[depth] += 1

  # Reset the section number when done processing the current level
  if depth >= 0:
    current_section_numbers[depth] = config.start_chap_num

  index_rst.write("\n")

# Processes a module
#   - config - a dictionary containing all the configuration options
#   - index_rst - the index.rst file being generated
#   - mod_path - the path to the module relative to the RST/source
#   - mod_attrib - dictionary containing the module data, 'exercises' is a mandatory field (even if its empty)
#   - depth - the depth of the recursion, used to determine the number of spaces to print before the module name to ensure proper indentation
#   - current_section_numbers - a list that contains the numbering scheme for each section or module ([chapter].[section].[...].[module])
#   - section_name - a string passed to modules for inclusion in the RST header that specifies which chapter / section the module belongs to
def process_module(config, index_rst, mod_path, mod_attrib={'exercises':{}}, depth=0, current_section_numbers=[], section_name=''):
  global todo_list
  global images
  global missing_exercises
  global satisfied_requirements
  global module_chap_map
  global num_ref_map

  # Parse the name of the module from mod_path and remove the file extension if it exists
  mod_name = os.path.splitext(os.path.basename(mod_path))[0]

  # Update the reference for each section to point to the first module in the section
  if section_name != '' and num_ref_map[section_name] == -1:
    num_ref_map[section_name] = mod_name

  # Print error message and exit if duplicate module name is detected
  if mod_name in processed_modules:
    print 'ERROR: Duplicate module name detected, module: ' + mod_name
    sys.exit(1)

  # Add module to list of modules processed
  processed_modules.append(mod_name)

  print ("  " * depth) + mod_name
  index_rst.write("   %s\n" % mod_name)

  # Initialize the module
  module = ODSA_RST_Module(config, mod_path, mod_attrib, satisfied_requirements, section_name, depth, current_section_numbers)

  # Append data from the processed module to the global variables
  todo_list += module.todo_list
  images += module.images
  missing_exercises += module.missing_exercises
  satisfied_requirements += module.requirements_satisfied
  num_ref_map = dict(num_ref_map.items() + module.num_ref_map.items())

  # Maps the chapter name and number to each module, used for correcting the numbers during postprocessing
  # Have to ignore the last number because that is the module number (which is already provided by Sphinx)
  module_chap_map[mod_name] = [section_name, '.'.join(str(i) for i in current_section_numbers[:-1])]

  # Hack to maintain the same numbering scheme as the old preprocessor
  mod_num = ''
  if len(current_section_numbers) > 0:
    mod_num = '%s.%d' % ('.'.join(str(j) for j in current_section_numbers[:-1]), (current_section_numbers[-1] + 1))

  num_ref_map[mod_name] = mod_num


def generate_index_rst(config, slides = False):
  """Generates the index.rst file, calls process_section() on config.chapters to recursively process all the modules in the book (in order), as each is processed it is added to the index.rst"""

  print "Generating index.rst\n"
  print "Processing..."

  header_data = {}
  header_data['mod_name'] = 'index'
  header_data['dispModComp'] = 'false'
  header_data['long_name'] = 'Contents'
  header_data['mod_chapter'] = ''
  header_data['mod_date'] = str(datetime.datetime.now()).split('.')[0]
  header_data['unicode_directive'] = rst_header_unicode if not slides else ''

  # Generate the index.rst file
  with open(config.book_src_dir + 'index.rst', 'w+') as index_rst:
    index_rst.write(index_header.format(config.start_chap_num))
    index_rst.write(rst_header % header_data)

    # Process all the chapter and module information
    process_section(config, config.chapters, index_rst, 0)

    index_rst.write(".. toctree::\n")
    index_rst.write("   :maxdepth: 3\n\n")

    # Process the Gradebook as well
    if not slides:
      process_module(config, mod_path='Gradebook', index_rst=index_rst)

    # If a ToDo file will be generated, append it to index.rst
    if len(todo_list) > 0:
      index_rst.write("   ToDo\n")

    index_rst.write("\n")
    index_rst.write("* :ref:`genindex`\n")
    index_rst.write("* :ref:`search`\n")


def generate_todo_rst(config, slides = False):
  """Sorts the list of ToDo directives (generated while recursively processing each module) by type and writes them all out to a file"""
  print '\nGenerating ToDo file...'

  # Sort the list of todo items by type (module_name, type, todo_directive)
  sorted_todo_list = sorted(todo_list, key=lambda todo: todo[1])

  with open(''.join([config.book_src_dir, 'ToDo.rst']), 'w') as todo_file:
    header_data = {}
    header_data['mod_name'] = 'ToDo'
    header_data['long_name'] = 'ToDo'
    header_data['dispModComp'] = False
    header_data['mod_chapter'] = ''
    header_data['mod_date'] = str(datetime.datetime.now()).split('.')[0]
    header_data['unicode_directive'] = rst_header_unicode if not slides else ''
    todo_file.write(rst_header % header_data)
    todo_file.write(todo_rst_template)

    # RST syntax for a horizontal rule (<hr />)
    hr = '\n----\n'
    current_type = ''

    for (mod_name, todo_type, todo_directive) in sorted_todo_list:
      if todo_type == '':
        todo_type ='No Category'

      # Whenever a new type is encountered, print a header for that type (using RST syntax)
      if current_type != todo_type:
        todo_file.writelines('\n'.join([hr, todo_type, '=' * len(todo_type), hr, '\n']))
        current_type = todo_type

      # Write a header with the name of the file where the ToDo originated (using RST syntax)
      source = 'source: ' + mod_name
      todo_file.writelines('\n'.join([source, '-' * len(source), '\n']))

      # Write the TODO directive itself
      todo_file.writelines(todo_directive)


def initialize_output_directory(config):
  """Creates the output directory (if applicable) and copies the necesssary files to it"""
  # Create the output directory if it doesn't exist
  # Will actually create '<build_dir>/<book_name>/source/Images/'
  distutils.dir_util.mkpath(config.book_src_dir + 'Images/')

  # Copy _static and select images from RST/source/Images/ to the book source directory
  distutils.dir_util.copy_tree(config.odsa_dir + 'RST/source/_static/', config.book_src_dir + '_static', update=1)

  # Copy config file to _static directory
  distutils.file_util.copy_file(config.config_file_path, config.book_src_dir + '_static/')

  # Create source/_static/config.js in the output directory
  # Used to set global settings for the client-side framework
  with open(config.book_src_dir + '_static/config.js','w') as config_js:
    config_js.writelines(config_js_template % config)

  # Create an index.html page in the book directory that redirects the user to the book_output_dir
  with open(config.book_dir + 'index.html','w') as index_html:
    index_html.writelines(index_html_template % config.rel_book_output_path)

  #Save the config file in the book directory, it will be use to send book components to the server
  # TODO: Why are we creating another copy of the config file when we already have it in _static?
  with open(config.book_dir + 'bookdata.json1','w') as book_json:
    book_json.writelines(json.dumps(config, default=lambda o: o.__dict__))


def initialize_conf_py_options(config, slides):
  """Initializes the options used to generate conf.py"""
  options = {}
  options['title'] = config.title
  options['book_name'] = config.book_name
  options['backend_address'] = config.backend_address
  options['module_origin'] = config.module_origin
  options['theme_dir'] = config.theme_dir
  options['theme'] = config.theme
  options['odsa_dir'] = config.odsa_dir
  options['book_dir'] = config.book_dir
  options['code_dir'] = config.code_dir
  options['code_lang'] = config.code_lang
  options['av_root_dir'] = config.av_root_dir
  options['exercises_root_dir'] = config.exercises_root_dir
  # The relative path between the ebook output directory (where the HTML files are generated) and the root ODSA directory
  options['eb2root'] = os.path.relpath(config.odsa_dir, config.book_dir + config.rel_book_output_path) + '/'
  options['rel_book_output_path'] = config.rel_book_output_path
  options['slides_lib'] = 'hieroglyph' if slides else ''

  return options


def configure(config_file_path, slides = False):
  """Configure an OpenDSA textbook based on a validated configuration file"""
  global satisfied_requirements

  print "Configuring OpenDSA, using " + config_file_path# + '\n'

  # Load the configuration
  config = ODSA_Config(config_file_path)

  # Add the list of topics the book assumes students know to the list of fulfilled prereqs
  if config.assumes:
    satisfied_requirements += [a.strip() for a in config.assumes.split(';')]

  # Optionally rebuild JSAV
  if config.build_JSAV:
    print "Building JSAV\n"
    status = 0

    with open(os.devnull, "w") as fnull:
      status = subprocess.check_call('make -s -C %s' % (config.odsa_dir + 'JSAV/'), shell=True, stdout=fnull)

    if status != 0:
      print "JSAV make failed"
      print status
      sys.exit(1)

  print "Writing files to " + config.book_dir + "\n"

  # Initialize output directory, create index.rst, and process all of the modules
  initialize_output_directory(config)
  generate_index_rst(config, slides)

  # Print out a list of any exercises found in RST files that do not appear in the config file
  if len(missing_exercises) > 0:
    print "\nExercises Not Listed in Config File:"

    for exercise in missing_exercises:
      print '  ' + exercise

  # Entries are only added to todo_list if config.suppress_todo is False
  if len(todo_list) > 0:
    generate_todo_rst(config, slides)

  # Dump num_ref_map to table.json to be used by the Sphinx directives
  with open(config.book_dir + 'table.json', 'w') as num_ref_map_file:
    json.dump(num_ref_map, num_ref_map_file)

  # Dump module_chap_map to page_chapter.json to be used by the avmetadata directive
  # NOTE: avmetadata is deprecated (it was used to generate the concept map but is no longer used)
  # If avmetadata is eventually removed, we can stop writing this file
  with open(config.book_dir + 'page_chapter.json', 'w') as page_chapter_file:
    json.dump(module_chap_map, page_chapter_file)

  # Initialize options for conf.py
  options = initialize_conf_py_options(config, slides)

  # Create a Makefile in the output directory
  with open(config.book_dir + 'Makefile','w') as makefile:
    makefile.writelines(makefile_template % options)

  # Create conf.py file in output source directory
  with open(config.book_src_dir + 'conf.py','w') as conf_py:
    conf_py.writelines(conf % options)

  # Copy only the images used by the book from RST/source/Images/ to the book source directory
  for image in images:
    distutils.file_util.copy_file(config.odsa_dir + 'RST/source/Images/' + image, config.book_src_dir + 'Images/')

  # Optionally run make on the output directory
  if config.build_ODSA:
    print '\nBuilding textbook...'

    if slides:
      proc = subprocess.Popen(['make', '-C', config.book_dir, 'slides'], stdout=subprocess.PIPE)
    else:
      proc = subprocess.Popen(['make', '-C', config.book_dir], stdout=subprocess.PIPE)
    for line in iter(proc.stdout.readline,''):
      print line.rstrip()

    # Calls the postprocessor to update chapter, section, and module numbers
    update_TOC(config.book_src_dir, config.book_dir + config.rel_book_output_path, module_chap_map)

    # Copy the registration page in the html directory
    distutils.file_util.copy_file(config.odsa_dir + 'lib/RegisterBook.html', config.book_dir + config.rel_book_output_path )

# Code to execute when run as a standalone program
if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-s", "--slides", help="Causes configure.py to create slides", dest="slides", action="store_true")
  (options, args) = parser.parse_args()

  if options.slides:
    os.environ['SLIDES'] = 'yes'
  else:
    os.environ['SLIDES'] = 'no'

  # Process script arguments
  if len(sys.argv) > 3:
    print "Invalid config filename"
    print "Usage: " + sys.argv[0] + " [-s] config_file_path"
    sys.exit(1)

  configure(args[0], options.slides)
