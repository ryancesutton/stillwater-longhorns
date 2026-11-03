# Reviewed Opponent Aliases

Reviewed November 1, 2026 using official university/athletics pages. Runtime map: [team_aliases.json](../web/team_aliases.json). These are search labels, not new football records or replacements for CFBD identifiers. Source URLs are provenance for a maintained configuration file; the app does not fetch them.

Canonical CFBD names are always accepted. Additional accepted forms:

| CFBD opponent | Additional forms | Official source checked |
| --- | --- | --- |
| Rice | Rice University | [Rice](https://www.rice.edu/) |
| Alabama | University of Alabama; Bama | [University](https://www.ua.edu/), [athletics word marks](https://rolltide.com/documents/download/2018/6/28/alabama-logos.pdf) |
| Wyoming | University of Wyoming; UW | [Wyoming](https://www.uwyo.edu/) |
| Baylor | Baylor University | [Baylor](https://www.baylor.edu/) |
| Kansas | University of Kansas; KU | [KU style guide](https://brand.ku.edu/guidelines/editorial/university-style-guide) |
| Oklahoma | University of Oklahoma; OU | [Oklahoma](https://www.ou.edu/) |
| Houston | University of Houston; UH | [Houston](https://www.uh.edu/) |
| BYU | Brigham Young University; Brigham Young | [BYU editorial style](https://styleguide.byu.edu/brand-guidelines/byu-terms/) |
| Kansas State | Kansas State University; K-State; K State | [K-State style guide](https://www.k-state.edu/communications-marketing/brand-style/voice-style/style-guide/index.html) |
| TCU | Texas Christian University; Texas Christian | [TCU](https://www.tcu.edu/) |
| Iowa State | Iowa State University; ISU | [University](https://www.iastate.edu/), [ISU usage](https://financialaid.iastate.edu/tools-and-resources/faqs/) |
| Texas Tech | Texas Tech University; TTU | [Texas Tech](https://www.ttu.edu/) |
| Oklahoma State | Oklahoma State University; OSU | [OSU athletics branding](https://static.okstate.com/custompages/branding/) |
| Washington | University of Washington; UW | [Washington](https://www.washington.edu/) |

`Brigham Young` and `Texas Christian` are intentionally accepted shortened forms of the sourced full names. `K State` is a punctuation-normalized form of K-State. Accepted search labels need not be preferred editorial forms. KSU and OK State are not in this initial curated list; do not assume every abbreviation or nickname is supported.

## Ambiguity and context

- UW has two candidates in the actual imported schedule: Wyoming and Washington. Bare UW asks for clarification. A full name alongside UW or a consistent season game number can disambiguate.
- OSU is also used by [Ohio State](https://www.osu.edu/) and [Oregon State](https://oregonstate.edu/). Both are recorded as ambiguity candidates, not imported opponents. With only Oklahoma State present, OSU resolves to that game. If multiple OSU candidates are imported later, the same resolver rejects a single automatic choice.
- Names are matched against imported game records, not a model's confidence score. Full mentions take priority over contained substrings: Oklahoma State does not become Oklahoma, and Kansas State does not become Kansas. Separate mentions such as Oklahoma **and** Oklahoma State remain conflicting constraints.
- A request for a team with no imported game does not create a record or trigger online research. If multiple games against the same opponent exist in future coverage, an opponent alone also requires clarification.
- Other shared acronyms may exist. This is a reviewed list for Texas 2023, not an exhaustive worldwide university-name registry. Expanding coverage requires reviewing the catalog and collision tests, including known candidates not yet represented here.

Normalization handles capitalization, periods, punctuation separators, and repeated spaces. There is no fuzzy spelling correction, live web lookup, automatic learning, or agent write access to this map. Unknown phrasing can still be rejected; this is not a general language parser.

## Maintenance

Add aliases through an ordinary reviewed code/configuration change: verify the institution with a primary source, preserve its canonical identity, record the URL and review date, examine collisions, and add match plus rejection tests. Do not ingest an entire web page or its instructions into the runtime catalog. Source references support name identity, not universal uniqueness or the user's intended meaning.

The optional developer check `node tests/test_game_search.js` now covers the original 15 query cases, 54 unambiguous canonical/alias matches, 17 normalization/context/collision cases, 16 additional nickname/context cases, and preservation of input order (102 query cases plus the order assertion). Running the app needs no Node runtime or packages. Database authorization is tested independently in Python/MySQL.

## Mascot and team-nickname extension

Catalog version 2 adds the reviewed labels below in `mascot_aliases`. This means team nicknames, not every costumed mascot character, singular form, or fan expression. Existing canonical names and IDs are unchanged. Research sources establish usage, not worldwide exclusivity.

| Opponent | Added team labels | Official source checked |
| --- | --- | --- |
| Rice | Owls | [Rice athletics](https://riceowls.com/) |
| Alabama | Crimson Tide; Tide | [Alabama word marks](https://rolltide.com/documents/download/2018/6/28/alabama-logos.pdf) |
| Wyoming | Cowboys; Pokes | [Wyoming football](https://gowyo.com/news/2026/8/24/football-cowboys-enter-final-week-of-fall-camp) |
| Baylor | Bears | [Baylor athletics](https://baylorbears.com/) |
| Kansas | Jayhawks | [Kansas athletics](https://kuathletics.com/) |
| Oklahoma | Sooners | [Oklahoma athletics](https://soonersports.com/) |
| Houston | Cougars; Coogs | [Houston traditions](https://uhcougars.com/sports/2018/6/12/trads-hou-traditions-html) |
| BYU | Cougars; Cougs | [BYU athletics](https://byucougars.com/soccer-cougs-in-the-pros) |
| Kansas State | Wildcats | [K-State athletics](https://www.kstatesports.com/) |
| TCU | Horned Frogs; Frogs | [TCU athletics](https://gofrogs.com/) |
| Iowa State | Cyclones | [Iowa State athletics](https://cyclones.com/) |
| Texas Tech | Red Raiders | [Texas Tech athletics](https://texastech.com/) |
| Oklahoma State | Cowboys; Cowpokes; Pokes | [Oklahoma State traditions](https://okstate.com/sports/2015/3/17/GEN_201401011?path=mbball) |
| Washington | Huskies | [Washington athletics](https://gohuskies.com/) |

Bare Cowboys and Pokes match Wyoming/Oklahoma State; Cougars matches BYU/Houston. These return clarification, not a guess. A fuller name such as `Wyoming Pokes`, `BYU Cougars`, or a consistent season game number narrows the candidate set. Contradictory combinations are rejected. Cougs and Coogs are separate reviewed spellings; no fuzzy substitution equates them. Cowpokes currently maps to Oklahoma State in this catalog; it is not claimed to be unique in all football usage.

[Washington State athletics](https://wsucougars.com/) also uses Cougs/Cougars. It is recorded as a known ambiguity candidate, not an imported game. A synthetic expansion test verifies that adding a Washington State game makes bare Cougs ambiguous. Other schools can share nicknames; coverage expansion must include reviewing those collisions before relying on the map. Frogs is an intentionally shortened search form of Horned Frogs. No runtime internet access, database changes, new credentials, or paid model calls were required for this extension.
