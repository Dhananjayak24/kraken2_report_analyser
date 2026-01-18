# kraken2_report_analyser
Kraken2 Report Analyser is a Python-based tool for parsing, restructuring, and summarizing kraken2 report output into biologically meaningful, analysis-ready tables and Excel workbook
The tool reconstructs the full taxonomic hierarchy from Kraken2 reports, computes accurate abundance and relative abundance metrics, and generates domain(Bacteria, Archaea, Fungi, Virus) and rank-specific(Domain, Phylum, Class, Order, Family, Genus, Species) outputs suitable for downstream analysis, visualization, and reporting.

This project is designed as a lightweight, extensible alternative to R/Shiny-based tools such as Pavian, with a focus on transparency, reproducibility, and pipeline integration.
# 1. Introduction

Kraken2 report files contain rich taxonomic information, but they are extremely difficult to filter or summarize using simple tools. Extracting domain-specific or rank-specific information (such as species, genus, or family) while also calculating correct relative abundance values usually requires custom scripting or manual post-processing. Despite Kraken2 being widely used, there has been a clear gap in lightweight tools that can generate domain-aware, rank-aware summaries with relative abundance values in a single, structured output.

This project aims to address that gap by providing a transparent, pipeline-friendly Python implementation that converts Kraken2 reports into organized, easy-to-interpret outputs suitable for downstream analysis and reporting.

# 2. Features

- Parses Kraken2 report files and reconstructs the full taxonomic hierarchy using indentation depth(Provides lineage: Domain>Phylum>Class>Order>Family>Genus>species/sub species)

- Automatically infers domains (Bacteria, Archaea, Viruses, Fungi) from taxonomic lineage

- Generates domain-specific outputs, with one file per domain

- Produces rank-specific summaries for phylum, class, order, family, genus, and species

- Calculates relative abundance independently within each rank and domain

- Uses clade-level read counts to ensure biologically meaningful abundance estimates

- Outputs structured Excel workbooks with separate sheets for each taxonomic rank


# 3. Usage

The tool is executed from the command line.
```
python kraken2_report_analyser.py <kraken_report_file> <sample_name> <output_path>
```

For example:

```
python kraken2_report_analyser.py sample.report sample_1 results/
```

# 4. Outputs

For each input Kraken2 report, the tool generates multiple CSV files organized by domain and taxonomic rank. Each file contains records for a single domain–rank combination and includes clade-level read counts and relative abundance values.

**Domain and Rank Specific Files**

For each domain (Bacteria, Archaea, Viruses, Fungi), the following CSV files are generated:

- <sample>_bacteria_phylum.csv
- <sample>_bacteria_class.csv
- <sample>_bacteria_order.csv
- <sample>_bacteria_family.csv
- <sample>_bacteria_genus.csv
- <sample>_bacteria_species.csv
- <sample>_archaea_phylum.csv
- <sample>_archaea_class.csv
- <sample>_archaea_order.csv
- <sample>_archaea_family.csv
- <sample>_archaea_genus.csv
- <sample>_archaea_species.csv
- <sample>_viruses_phylum.csv
- <sample>_viruses_class.csv
- <sample>_viruses_order.csv
- <sample>_viruses_family.csv
- <sample>_viruses_genus.csv
- <sample>_viruses_species.csv
- <sample>_fungi_phylum.csv
- <sample>_fungi_class.csv
- <sample>_fungi_order.csv
- <sample>_fungi_family.csv
- <sample>_fungi_genus.csv
- <sample>_fungi_species.csv

Each CSV file contains data only for the specified domain and rank.

## 4.1 CSV File Contents

Each output CSV file includes the following columns:

- `sample` – Sample identifier provided at runtime
- `domain` – Taxonomic domain inferred from lineage
- `rank` – Taxonomic rank (P, C, O, F, G, or S)
- `tax_id` – NCBI taxonomy identifier
- `name` – Taxon name
- `reads_clade` – Number of reads assigned to the taxon and all its descendants
- `relative_abundance` – Relative abundance calculated within the file
- `lineage` – Full taxonomic lineage reconstructed from the Kraken2 report

Relative abundance values are normalized independently within each CSV file, ensuring that abundance estimates are specific to the given domain and rank.

### Notes on Abundance Interpretation

- Read counts are derived from `reads_clade`, reflecting the total reads assigned to a taxon and its child nodes.

- Totals may differ across taxonomic ranks due to reads being classified at different levels of confidence(Species-level totals are not expected to match genus-, family-, or phylum-level totals.)
