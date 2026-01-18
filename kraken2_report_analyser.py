print("Om Namah Shivaya")

import argparse
import os
import sys
import csv
import pandas as pd

#Domain keywords to divide the data based on domains
domain_keywords = {
    "Bacteria": ["bacteria"],
    "Archaea": ["archaea"],
    "Fungi": ["fungi, fungus"],
    "Virus": ["virus", "viruses"]
}

rank_dict = {
    "P": "phylum",
    "C": "class",
    "O": "order",
    "F": "family",
    "G": "genus",
    "S": "species"
}

def parse_arguments():
    #HEre the arguments are taken using argparse library
    #It returns the files parsed as string
    parser = argparse.ArgumentParser(
        description="Kraken2 report analyser"
    )

    parser.add_argument(
        "report_file",
        help="Path to Kraken2.report file"
    )
    parser.add_argument(
        "sample_name",
        help="The name in which the files to be stored as"
    )
    parser.add_argument(
        "output_path",
        help="The directory location where files are to be saved"
    )
    args = parser.parse_args()
    return args.report_file, args.sample_name, args.output_path

def input_validation(report_file, output_path):
    #validating the input arguments
    if not os.path.isfile(report_file):
        print(f"ERROR: Report file is not found: {report_file}")
        sys.exit(1)
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)

def parse_report_line(line):
    #This function will take each line, fetch depth, percent, reads_clade, reads_taxon, rank, taxid, name
    raw_line = line.rstrip("\n")

    #split by tab space
    columns = raw_line.split("\t")

    #Check if number of columns is 6
    if len(columns) < 6:
        return None
    try:
        name_field = columns[5]
        #counting depth
        leng_before = len(name_field)
        leng_after = len(name_field.lstrip(" "))
        depth = ((leng_before - leng_after) // 2)
        parsed = {
            "percent": float(columns[0]),
            "reads_clade": int(columns[1]),
            "reads_taxon": int(columns[2]),
            "rank": columns[3],
            "tax_id": int(columns[4]),
            "name": name_field.strip(),
            "depth": depth
            #"lenght_before": leng_before,
            #"length_after": leng_after
        }
    except ValueError:
        return None
    return parsed

def parse_report_file(report_file):
    #This is the main fucntion which takes report file and passes it to paese_report_line() function line by line
    parsed_rows = []

    with open(report_file, "r") as rf:
        for line_num,  line in enumerate(rf, start=1):
            #skip empty lines
            if not line.strip():
                continue
            parsed = parse_report_line(line)

            if parsed is None:
                continue
            
            parsed_rows.append(parsed)

    return parsed_rows

#Building lineage
def build_lineage(parsed_rows):
    #Here we eill use stack method principle where we will push or pop last values from a list based on depth
    #This takes in parsed_rows adds lineage into dictionary and returns the same parsed_rows
    lineage_stack = []

    for row in parsed_rows:
        depth = row["depth"]
        name = row["name"]

        #skip unclassified rows
        if row["rank"] == "U":
            row["lineage"] = "unclassified"
            continue
        #We will see whether depth is matching with stack lenght, this is done because,
        #If suppose the Family changes as we go down then the stack will be rebuilt by
        #removing values after that depth so that older data for previous family and genus are removed.
        while len(lineage_stack) > depth:
            lineage_stack.pop()

        #If depth is equal to stack length then push the name
        if len(lineage_stack) == depth:
            lineage_stack.append(name)
        else:
            #If depth > stack length, this is rare but sometimes due to no rank it might  happen, in that case
            #It will keep the contents in the lineage_stack till the depth length and then append the next name
            lineage_stack = lineage_stack[:depth]
            lineage_stack.append(name)

        #Build lineage
        row["lineage"] = ">".join(lineage_stack)

    return parsed_rows

def extract_domain(parsed_rows):

    for row in parsed_rows:
        lineage = row.get("lineage", "")

        #by default we will keep it unclassified
        domain = "unclassified"

        if lineage == "unclassified":
            row["domain"] = domain
            continue
        
        for dom, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in lineage.lower():
                    domain = dom
                    break
                if domain != "unclassified":
                    break
        row["domain"] = domain

    return parsed_rows

def filter_rows(rows, domain=None, rank=None):
    #Filter rows by domain or rank or both
    filtered = []

    for row in rows:
        if domain is not None:
            if row.get("domain") != domain:
                continue
        if rank is not None:
            if row.get("rank") != rank:
                continue
        filtered.append(row)
    
    return(filtered)

def compute_relative_abundance(rows):
    #Compute relative abundance for a list of rows based on reads_clade.

    total_reads = sum(row["reads_clade"] for row in rows)

    # Avoid division by zero
    if total_reads == 0:
        for row in rows:
            row["relative_abundance"] = 0.0
        return rows

    for row in rows:
        row["relative_abundance"] = (row["reads_clade"] / total_reads)*100

    return rows

#helper function for write domain excel function
def rows_to_dataframe(rows):
    """
    Convert parsed rows to a pandas DataFrame.
    """

    data = []

    for row in rows:
        data.append({
            "domain": row["domain"],
            "rank": row["rank"],
            "tax_id": row["tax_id"],
            "name": row["name"],
            "reads_clade": row["reads_clade"],
            "relative_abundance": row["relative_abundance"],
            "lineage": row["lineage"]
        })

    return pd.DataFrame(data)


def write_domain_excel(rows, domain, sample_name, output_path, rank_map):
    # Write one Excel file per domain with multiple sheets

    domain_rows = [r for r in rows if r.get("domain") == domain]

    if not domain_rows:
        print(f"No data for domain {domain}, skipping Excel file.")
        return

    output_file = os.path.join(output_path, f"{sample_name}_{domain.lower()}.xlsx")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for rank, rank_name in rank_map.items():

            subset = filter_rows(domain_rows, rank=rank)

            if not subset:
                continue

            subset = compute_relative_abundance(subset)
            df = rows_to_dataframe(subset)

            df.to_excel(writer, sheet_name=rank_name, index=False)

    print(f"Written Excel file: {output_file}")

def write_csv(rows, output_file, sample_name):
    """
    Write rows to CSV file.
    """

    if not rows:
        return

    fieldnames = [
        "domain",
        "rank",
        "tax_id",
        "name",
        "reads_clade",
        "relative_abundance",
        "lineage"
    ]

    with open(output_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "domain": row["domain"],
                "rank": row["rank"],
                "tax_id": row["tax_id"],
                "name": row["name"],
                "reads_clade": row["reads_clade"],
                "relative_abundance": row["relative_abundance"],
                "lineage": row["lineage"]
            })

def main():
    report_file, sample_name, output_path = parse_arguments()
    input_validation(report_file, output_path)

    print("Input parameters are:")
    print(f"     Report file: {report_file}")
    print(f"     Sample Name: {sample_name}")
    print(f"     Output path: {output_path}")

    parsed_data_1 = parse_report_file(report_file)
    parsed_data_2 = build_lineage(parsed_data_1)
    parsed_data_3 = extract_domain(parsed_data_2)

    #final combinations of files to be saved using all domain and all ranks
    for domain in domain_keywords:
        write_domain_excel(rows=parsed_data_3, domain=domain, sample_name=sample_name, output_path=output_path, rank_map=rank_dict)

    #writing all species file
    all_species = filter_rows(parsed_data_3, rank="S")
    all_species = compute_relative_abundance(all_species)

    output_file = os.path.join(
        output_path,
        f"{sample_name}_all_species.csv"
    )
    write_csv(all_species, output_file, sample_name)


    '''
    bacteria_species = filter_rows(parsed_data_3, domain="Bacteria", rank="S")
    viral_genus = filter_rows(parsed_data_3, domain="Viruses", rank="G")
    bacteria_all = filter_rows(parsed_data_3, domain="Bacteria")
    all_species = filter_rows(parsed_data_3, rank="S")

    print(f"\nBacteria species count: {len(all_species)}")

    for row in all_species[:5]:
        print(row["name"], row["reads_clade"])
    print(f"Parsed {len(parsed_data_3)} rows from kraken report")

    print(f" First 10 rows:\n")
    for row in parsed_data_3[:10]:
        print(row)
        #print(parsed_data.name)'''

if __name__ == "__main__":
    main()