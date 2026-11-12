# History basemap library

Simplified polity outlines taken from [Historical Basemaps](https://github.com/aourednik/historical-basemaps) by André Ourednik. That repository is GPL-3.0, and so is this one.

LearnWhale draws these files for years the source already stores. The files stay here. They are not copied into the LearnWhale source. Coastlines and years this set does not cover stay with their own sources: Natural Earth, the Ancient World Mapping Center, and Cliopatria.

`build.py` downloads the source year files and writes one GeoJSON file per polity. `borderPrecision` is the source value: 1 is approximate, 2 is moderate, and 3 was set by a treaty or law.

The stored years in this library are 500 BCE, 1279, and 1783. A year that is not here is not invented.
