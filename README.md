<h1 align="center"> scene-search </h1>

<p align="center"> A semantic search engine built for film-makers who think in scenes.</p>

<img src="https://i.pinimg.com/originals/64/13/3f/64133f9d37e36786d3e91a70ea3e2dd3.gif" width="2000">

### TLDR; What is **scene-search**?
- Bilingual search engine for post-production footage.
- Indexes footage using transcripts, supports natural language queries, returns clips with timestamps and relevance ranking.

### How does scene-search work?
```text
scene-search/
├── static/
│   ├── scene-search.png
│   └── setup.md
│   ├── scene-search.png
├── templates/
│   ├── main.py
│   └── utils.py
├── uploads/
│   └── test_main.py
│   └── setup.md
├── utils/
│   ├── audio.py
│   └── whisper.py
└── LICENSE
```

<h3> How to Run? </h3>
1. Make sure you are in the root folder. <br> <br>
<pre>cd scene-search</pre>
2. Make sure you have all your dependencies installed. <br> <br>
<pre>pip install -r requirements.txt</pre>
3. To run the app with the database, use the following command. <br> <br>
<pre>python app.py</pre>