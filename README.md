# Coptic Dictionary Online

The dictionary comprised of the XML Coptic lexicon created by the BBAW and interface by Coptic SCRIPTORIUM.  Currently deployed at https://coptic-dictionary.org/

Lexicon data licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), software under the Apache 2.0 license (https://www.apache.org/licenses/LICENSE-2.0) (see below)

## About the dictionary

#### Lexicon preparation

The new *Comprehensive Coptic Lexicon* is a combination of two parts: the *BBAW Lexicon of Coptic Egyptian* of the project Strukturen und Transformationen des Wortschatzes der ägyptischen Sprache at the Berlin-Brandenburgische Akademie der Wissenschaften, Berlin, Germany, which includes etymologically Egyptian lexemes of Coptic, and the *DDGLC Lexicon of Greek Loanwords in Coptic* of the project Database and Dictionary of Greek Loanwords in Coptic at the Ägyptologisches Seminar, Freie Universität Berlin, Germany. Both projects are led by Prof. Tonio Sebastian Richter. The following people mainly contributed to compiling the lexical data:

  * Dylan M. Burns (DDGLC)
  * Frank Feder (BBAW, AdWG)
  * Katrin John (DDGLC)
  * Maxim Kupreyev (BBAW)

moreover

  * Mathew Almond, Marc Brose, Sonja Dahlgren, Julien Delhez, Anne Grons, Joost Hagen, Jakob Höper, Mariana Jung, Elisabeth Koch, Lena Krastel, Frederic Krueger, Jan Moje, Franziska Naether, Anne Sörgel, Nina Speranskaja, Gunnar Sperveslage, Vincent Walter, Alberto Winterberg.

Each lexicon entry has a stable *Thesaurus Linguae Aegyptiae* (TLA) ID no.

TEI XML compliant data files of the lexica are published  under a [CC BY-SA 4.0 Int.](https://creativecommons.org/licenses/by-sa/4.0/) license at DOI [10.17169/refubium-2333](https://doi.org/10.17169/refubium-2333).

#### Search interface

The search interface was designed at Georgetown University as part of the project KELLIA by:  

  * Emma Manning  
  * Amir Zeldes
  
Code for the interface is made available under the Apache software license, version 2.0 (https://www.apache.org/licenses/LICENSE-2.0)


#### Projects

  * [Strukturen und Transformationen des Wortschatzes der ägyptischen Sprache](https://www.saw-leipzig.de/de/projekte/strukturen-und-transformationen-des-wortschatzes-der-aegyptischen-sprache) (BBAW)
  * [KELLIA](http://kellia.uni-goettingen.de/) (BBAW, Georgetown, Göttingen, Münster, Pacific)  
  * [Coptic Scriptorium](http://copticscriptorium.org/) (Georgetown, Pacific)  
  * [Sonderforschungsbereich (SFB) 1136](http://www.uni-goettingen.de/de/517150.html) - Bildung und Religion in Kulturen des Mittelmeerraums und seiner Umwelt von der Antike bis zum Mittelalter und zum Klassischen Islam - [Teilprojekt B 05](http://www.uni-goettingen.de/de/521144.html) (Universität Göttingen)  

#### Funding agencies

  * [Deutsche Forschungsgemeinschaft](http://dfg.de) (DFG)  
  * [The National Endowment for the Humanities](https://www.neh.gov) (NEH)  


## Development

### Overview

The dictonary interfaces is built using npm / vite using React JS.  To run and develop locally, install the dependencies and run the dev server:

```bash
npm install
npm run dev
```

### Building lexical data

Ensure all lexical resources are up to date in `data/`. These are built using the Python scripts in `utils/`. In particular we assume the following already exist in `data/` (file names may change in the future as we add more dialect data):

 *  cache_freqs_lemma_bohairic.tab
 * cache_freqs_lemma_sahidic.tab
 * cache_freqs_norm_bohairic.tab
 * cache_freqs_norm_sahidic.tab
 * coptic_dict.xml
 * covered_base_forms.tab
 * egyptian_etymologies.tab
 * entities.json
 * examples_bohairic.tab
 * examples_sahidic.tab
 * hyperlemmas.tab
 * phrase_freqs_bohairic.tab
 * phrase_freqs_sahidic.tab
 * supplemental_entries.tab
 * tt_collocs_bohairic.tab
 * tt_collocs_sahidic.tab

Create a production build:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

For production builds note that you will need to first generate detailed entry-wise .json files like C1.json using `make_json.py`, and then *manually copy* `local-data/details/` to `details/` on the server, since Vite otherwise takes long to process the 10K+ individual json files. We use server.middlewares in vite.config.js to circumvent this issue in dev mode.

### Deploying to root or subfolders on a server

You can configure the deployment subfolder location on a server using:

- Environment variable: `CDO_BASE_PATH` (you can set it in a `.env.production` file)

It is read in `vite.config.js` and drives Vite's `base`. Runtime routing and static/data URLs then use `import.meta.env.BASE_URL`, so everything stays aligned.

Example values:

- Root deploy (`https://example.com/`):
  - `CDO_BASE_PATH=/`
- Single subfolder (`https://example.com/dictionary/`):
  - `CDO_BASE_PATH=/dictionary/`
- Nested subfolders (`https://example.com/tools/cdo/`):
  - `CDO_BASE_PATH=/tools/cdo/`

Trailing and leading slashes are normalized automatically by `vite.config.js`.

