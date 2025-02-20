import pandas as pd
from ics import Calendar, Event
from datetime import datetime

SGA = int(input("Enter your SGA Number: "))
TblFull = input("Enter your HAL Table Number: ")
TBL_NUMBER = int(TblFull[:-1])
TBL_LETTER = TblFull[-1]
def checkSGA(group):
    start, end = group[3:].split("-")
    if int(start) <= SGA <= int(end):
        return True
    else:
        return False

def checkTbl(group):
    # Check if group has an & in it
    if "&" in group:
        # Split the group into twoj
        group1, group2 = group.split(" & ")
        if checkTbl(group1) or checkTbl(group2):
            return True
        else:
            return False
    else:
        # Simple logic
        rng = group[4:].split("-")
        startNumber, endNumber = int(rng[0][:-1]), int(rng[1][:-1])
        startLetter, endLetter = rng[0][-1], rng[1][-1]
        if startLetter == endLetter:
            # Simple
            if startLetter == TBL_LETTER:
                if startNumber <= TBL_NUMBER <= endNumber:
                    return True
                else:
                    # Not in number range
                    return False
            else:
                # Different letter group
                return False
        else:
            # So both letters are involved, just check table number
            if startNumber <= TBL_NUMBER <= endNumber:
                return True
            else:
                return False

def checkGroup(row):
    # Placeholder function, replace with actual logic
    group = row["Group"]
    if pd.isna(group):
        # It's a lecture
        return True
    else:
        # It's a tutorial or lab
        typeOfGroup = group[:3]
        if typeOfGroup == "SGA":
            return checkSGA(group)
        elif typeOfGroup == "Tbl":
            return checkTbl(group)
        else:
            # Nutrition Lab
            if typeOfGroup == "Nut":
                return True
            else:
                print(f"Unknown group type: {group}")
        return False
    

def filter_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Filter rows based on checkGroup function
    filtered_df = df[df.apply(checkGroup, axis=1)]
    # Save the filtered data to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    # Get removed rows
    removed_df = df.loc[~df.index.isin(filtered_df.index)]
    
    # Save the filtered data to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    
    # Print removed rows
    # pd.set_option('display.max_rows', None)
    print(f'Removed {removed_df.shape[0]} rows')
    # print(removed_df) Print if you would like to see the removed rows
    
def create_ics(csv_file, ics_file):
    df = pd.read_csv(csv_file)
    calendar = Calendar()

    for _, row in df.iterrows():
        event = Event()
        if row["Session"] == "Lecture":
            event.name = f"{row.Module}: {row.Title}"
        else:
            event.name = f"{row.Module} {row.Session}: {row.Title}"  # Change column name as needed
        
        event.location = str(row["Venue"]) if pd.notna(row["Venue"]) else ""
        event.description = f"Staff: {row.Staff}"
        
        # Time
        event.begin = datetime.strptime(row["Date"] + " " + row["Start Time"], "%d %b %Y %I:%M %p")
        event.end = datetime.strptime(row["Date"] + " " + row["End Time"], "%d %b %Y %I:%M %p")
        calendar.events.add(event)

    with open(ics_file, "w") as f:
        f.writelines(calendar)

# Example usage
input_csv = "timetable.csv"  # Change this to your actual file path
output_csv = "output.csv"
ics_file = "events.ics"

filter_csv(input_csv, output_csv)
create_ics(output_csv, ics_file)


# fix ics file for timezone issues

import re

# Define the Auckland timezone block
TIMEZONE_BLOCK = """BEGIN:VTIMEZONE
TZID:Pacific/Auckland
BEGIN:STANDARD
DTSTART:20240407T030000
TZOFFSETFROM:+1300
TZOFFSETTO:+1200
TZNAME:NZST
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20240929T020000
TZOFFSETFROM:+1200
TZOFFSETTO:+1300
TZNAME:NZDT
END:DAYLIGHT
END:VTIMEZONE
"""

def fix_ics_timezone(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    # Check if timezone block already exists
    if any("VTIMEZONE" in line for line in lines):
        print("Timezone already defined, skipping addition.")
    else:
        # Find the position after VERSION:2.0 to insert the timezone block
        for i, line in enumerate(lines):
            if line.strip().startswith("VERSION:2.0"):
                lines.insert(i + 1, TIMEZONE_BLOCK + "\n")
                break

    # Update DTSTART and DTEND to include timezone
    updated_lines = []
    for line in lines:
        if line.startswith("DTSTART:") or line.startswith("DTEND:"):
            line = re.sub(r"(DTSTART|DTEND):(\d+)", r"\1;TZID=Pacific/Auckland:\2", line)
        updated_lines.append(line)

    # Write the fixed ICS file
    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(updated_lines)

    print(f"Fixed ICS file saved as: {output_file}")

# Example Usage:
fix_ics_timezone("events.ics", "mbchb.ics")