# LEUCHTLINIE Scraper

Scraping right-wing incidents in Baden-Württemberg, Germany as monitored by the NGO [LEUCHTLINIE](https://www.leuchtlinie.de).

-   Website: <https://www.leuchtlinie.de/chronik>
-   Data: <https://morph.io/rechtegewalt/leuchtlinie-scraper>

## Usage

For local development:

-   Install [poetry](https://python-poetry.org/)
-   `poetry install`
-   `poetry run python scraper.py`

For Morph:

-   `poetry export -f requirements.txt --output requirements.txt`
-   commit the `requirements.txt`
-   modify `runtime.txt`

## Morph

This is scraper runs on [morph.io](https://morph.io). To get started [see the documentation](https://morph.io/documentation).

## License

MIT
