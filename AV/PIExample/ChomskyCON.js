$(document).ready(function(){
    "use strict";
    var av_name = "ChomskyCON";
    var av = new JSAV(av_name);
    var arrow = String.fromCharCode(8594);
    var grammar =  "[\
        [\"&lt;sentence&gt;\",\"→\",\"&lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt;\"],\
        [\"&lt;verb&gt;\",\"→\",\"&lt;noun&gt;|&lt;article&gt;&lt;noun&gt;\"],\
        [\"&lt;d.o.&gt;\",\"→\",\"&lt;article&gt;&lt;noun&gt;|&lt;nounz&gt;\"],\
        [\"&lt;noun&gt;\",\"→\",\"Frits|ball\"],\
        [\"&lt;article&gt;\",\"→\",\"the|an|a\"]\
    ]";
        /****/
    /**<sentence> → <subject><verb><d.o.>
<subject> → <noun> | <article><noun>
<verb> → hit | ran | ate
<d.o.> → <article><noun> | <noun>
<noun> → Fritz | ball
<article>→ the | an | a
 */
var grammerArray = JSON.parse(grammar);
var lastRow = grammerArray.length;
grammerArray.push(["", arrow, ""]);
var grammerMatrix = av.ds.matrix(grammerArray, {style: "table", left: 10});

var injector = PIFRAMES.init(av_name);
// Load the config object with interpreter and code created by odsaUtils.js
var config = ODSA.UTILS.loadConfig({av_name: av_name}),
    interpret = config.interpreter, // get the interpreter
    code = config.code;             // get the code object
var goNext = false;
av.umsg("let's look at a grammar you can maybe relate to, a grammar for english. This will be a tiny subset of the english language, not complete by far!");
av.displayInit();
av.umsg(injector.injectQuestion("q1"));
av.step();

//second frame
av.umsg(injector.injectQuestion("q2", "Any grammar has variables (also called 'non-terminals') and terminals. Terminals are generally strings. Variables are things that ultimately are replaced by terminals."));
av.step();
////
av.umsg(injector.injectQuestion("q22","In this example, we put <> brackets around all of the variables to make them easier to recognize."));
av.step();

//second grammar
av.umsg(injector.injectQuestion("q3", "In this example, we put <> brackets around all of the variables to make them easier to recognize."));
av.step();

//thrid grammar
av.umsg(injector.injectQuestion("q4", "Grammars have a collection of productions. In this example, each production replaces a variable with some series of variables and terminals. "));
av.step();
///

av.umsg(injector.injectQuestion("q5", " All 'sentences' in the 'language' are generated by starting with the &lt;sentence&gt; variable and using productions to reach the desired sentence. Let’s derive “Fritz hit the ball” from"));
av.step();
////
av.umsg(injector.injectQuestion("q6", "The first step is to replace &lt;sentence&gt; with &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt;"));
av.step();

////
av.umsg(injector.injectQuestion("q7", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt;&lt;/d.o&gt;"));
av.step();

//////
av.umsg(injector.injectQuestion("q8", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt;&lt;/d.o&gt;"));
av.step();

//////
av.umsg(injector.injectQuestion("q9", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt; -> Fritz &lt;verb&gt;&lt;d.o&gt; -> Fritz hit &lt;d.o&gt;"));
av.step();

//////
av.umsg(injector.injectQuestion("q10", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt; -> Fritz &lt;verb&gt;&lt;d.o&gt; -> Fritz hit &lt;d.o&gt; -> Fritz hit &lt;article&gt;&lt;noun&gt;"));
av.step();

//////
av.umsg(injector.injectQuestion("q11", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt; -> Fritz &lt;verb&gt;&lt;d.o&gt; -> Fritz hit &lt;d.o&gt; -> Fritz hit &lt;article&gt;&lt;noun&gt; -> Fritz hit the &lt;noun&gt;"));
av.step();

//////
av.umsg(injector.injectQuestion("q12", "Continue substituting variables &lt;sentence&gt; -> &lt;subject&gt;&lt;verb&gt;&lt;d.o.&gt; -> &lt;noun&gt;&lt;verb&gt;&lt;d.o&gt; -> Fritz &lt;verb&gt;&lt;d.o&gt; -> Fritz hit &lt;d.o&gt; -> Fritz hit &lt;article&gt;&lt;noun&gt; -> Fritz hit the &lt;noun&gt;"));
av.step();

//////
av.umsg();
av.step();
av.umsg(injector.injectQuestion("q13", "The reason why we can derive “The ball hit Fritz”, and “The ball ate the ball” is that grammars only focus on the correct syntax sentences."));
av.step();

//////
av.umsg(injector.injectQuestion("q14"), "The formal definition of grammar is G=(V,T,S,P) where V is a finite set of variables (nonterminals) T is a finite set of terminals (generally, these are strings). S is the start variable (S∈V) P is a set of productions (rules) in the form x→y means to replace x by y");
av.step();

//////
av.umsg(injector.injectQuestion("q15", "The formal definition of grammar is G=(V,T,S,P) where V is a finite set of variables (nonterminals) T is a finite set of terminals (generally, these are strings). S is the start variable (S∈V) P is a set of productions (rules) in the form x→y means to replace x by y"));
av.step();

//////
av.umsg("W⇒z means that W derives string z, W⇒∗z means that W derives string z in 0 or more steps, W⇒+z means that W derives string z in 1 or more steps ");
av.step();
av.umsg("Given grammar: G=(V,T,S,P) where V is a finite set of variables (nonterminals) T is a finite set of terminals (generally, these are strings). S is the start variable (S∈V) P is a set of productions (rules) in the form x→y means to replace x by y");
av.step();
av.umsg(injector.injectQuestion("q15"));
av.step();


av.recorded();
});
