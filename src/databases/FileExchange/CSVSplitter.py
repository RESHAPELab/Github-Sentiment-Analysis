# Import libraries
import csv
import sys

def writeToCSV(output, fileName):
    # Write rows to the CSV file
    with open(fileName, "w") as csvFile:

        # Setup CSV writer
        csvWriter = csv.writer(csvFile)
        
        # Check if we have the column header
        if output[0][0] is not "bodyText":
            csvWriter.writerow(["bodyText"])

        # Write rows to CSV file
        csvWriter.writerows(output)

def outputHandler(output):
    # Create subfile name
    subfileName = fileNamePrefix + str(subfileCounter) + ".csv"

    # Output to screen
    print(f"[WORKING] Created {subfileName} with {len(output)} rows")

    # Writes to CSV file
    writeToCSV(output, subfileName)

if __name__ == "__main__":
    # Check if there aren't enough arguments given
    if len(sys.argv) < 3:
        print("[ERROR] Not enough arguments!")

    # Gets the file name from the command line
    inputFileName = sys.argv[1]

    # What to split every file by
    numToSplitCSV = int(sys.argv[2])

    # Get the prefix of the file name
    fileNamePrefix = inputFileName[:-4]

    # Set a counter to assist in naming subfiles
    subfileCounter = 0

    # Open CSV file
    with open(inputFileName) as csvFile:
        # Setup CSV Reader
        csvReader = csv.reader(csvFile)

        # Setup text to be written into CSV 
        output = list() 

        # Declare/Initialize line counter
        count = 0

        # Count each number and get each row
        for row in csvReader:

            # Add to output
            if count < numToSplitCSV:
                output.append(row)
                count = count + 1

            # Write to CSV
            elif count == numToSplitCSV:
                # write to file if at limit
                outputHandler(output)

                # Reset count and increase subfileCounter
                count = 0
                subfileCounter = subfileCounter + 1
                output = list()

        # Write to file if it is empty
        outputHandler(output)


