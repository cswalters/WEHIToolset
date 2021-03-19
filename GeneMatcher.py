"""
Mainly a program for extracting the identifier-data pairing in the excel worksheets.
Often identifiers such as gene names are stacked with semi-colons in a single data field.
This extracts them and then associates them each with a data entry.
Also contains function for matching the data with that in another list and
then outputting the common identifiers with the associated data.
"""

# Current target directory to draw input files from and to output results to.
FILEPATH = "/Users/chris/Documents/WEHI/SandraLab/Networks/Data/Cis+Socs1Narelle/Gene2Uniprot/"

# Input data of list of gene names and experimental dataset with gene names matched
# to Uniprot IDs and any other data desired.
GENE_FILE = "GeneNames.txt"
EXP_DATA = "ExperimentalDataTabbed.txt"

# Output text file in same folder.
OUT_FILE = "Matches.txt"


def main():

    #g_list = extract_input(FILEPATH + GENE_FILE)

    #matched = match_to_uniprot(FILEPATH + EXP_DATA, g_list)

    cleaned_data = extract_target(FILEPATH + EXP_DATA)

    write_to_file(FILEPATH + OUT_FILE, cleaned_data)

    return


# Iterate through file and make list of gene names contained.
# Takes .txt file with each entry on a new line. Considers each line as a single data field.
# Remove column titles.
def extract_input(gene_file):

    with open(gene_file) as file:

        gene_list = [line.rstrip().lower() for line in file]

    return gene_list


def match_to_uniprot(exp_file, gene_list):

    exp_data = {}

    with open(exp_file) as file:

        for line in file:

            line = line.split("\t")

            if line[0] == "leadingRazorProtein":
                continue

            names = line[8].split(";")

            for gene in gene_list:

                if names[0].lower() == gene:
                    exp_data[gene] = line[0]

    return exp_data


# Takes a .txt file with each entry on a new line.
# Use tab delimiting to determine how many data fields in line.
# Requires the matching identifier to be the first data field in the line.
# Remove column titles.
def extract_target(exp_file):

    exp_data = {}

    with open(exp_file) as file:

        for line in file:

            entries = line.split("\t")

            if entries[-1] in ["\n", ""]:
                entries = entries[:-1]

            print(entries)

            exp_data[entries[0].split(";")[0]] = entries[-1].rstrip('\n')

    return exp_data


# Takes a output file path (as a .txt) and an output dictionary.
# Writes it with each key-value pair on a new line.
def write_to_file(out_file, output):

    with open(out_file, "w") as out:

        out.write("Gene\tData\n")

        for gene in output.keys():
            out.write(gene.upper() + "\t" + output[gene] + '\n')


if __name__ == '__main__':
    main()

