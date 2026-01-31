<h1 align="center"> scene-search </h1>

<p align="center"> A semantic search engine built for film-makers who think in scenes.</p>

<img src="https://i.pinimg.com/originals/64/13/3f/64133f9d37e36786d3e91a70ea3e2dd3.gif" width="2000">

### TLDR; What is **scene-search**?
- Bilingual search engine for post-production footage.
- Indexes footage using transcripts, supports natural language queries, returns clips with timestamps and relevance ranking.

### Problems yet to fix
- Chunking and summarizing the chunks is too slow

### How does scene-search work?
`utils` has **three** main modules, `audio_conversion`, `audio_transcription`, `transcription_summarizer`.

<h3> How to Run? </h3>
1. Make sure you are in the root folder. <br> <br>
<pre>cd scene-search</pre>
1. Make sure you have all your dependencies installed. <br> <br>
<pre>pip install -r requirements.txt</pre>
1. To run the app with the database, use the following command. <br> <br>
<pre>python app.py</pre>