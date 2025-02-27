import re

def parse_cases(case_entries):
    """
    Given a list of raw case entry strings, extract relevant fields from each entry.
    
    Returns:
        A list of dictionaries, where each dict contains the parsed fields for one case.
    """

    # Compile the regular expressions we'll need:
    county_pattern = re.compile(r"In the District Court of\s+(.*?)\s+County")
    case_pattern = re.compile(r"The Case ID is\s+JV (\d{2}) (\d{7})\s+")
    docket_pattern = re.compile(r"Docket Number is (.+?)\s+(\S+)")
    # Capture lines that end with 'Minor' or 'Juvenile', ignoring leading spaces
    defendant_pattern = re.compile(r"^\s+(.*?)\s*,\s*(Minor|Juvenile|a Juvenile)\s*$", re.MULTILINE)
    judge_pattern = re.compile(r"The Honorable\s+(.*?),\s+presiding\.")
    classification_pattern = re.compile(r"Classification:\s+(.*)")
    filed_pattern = re.compile(r"Filed on\s+(\d{2}/\d{2}/\d{4})\s+by (.*?)")
    termination_pattern = re.compile(r"This case is Terminated as of\s+(\d{2}/\d{2}/\d{4})")

    results = []
    
    for entry in case_entries:
        data = {}
        
        # 1) County
        match_county = county_pattern.search(entry)
        if match_county:
            data["county"] = match_county.group(1).strip()
        else:
            data["county"] = ""
        
        # 2) Case ID and 3) Docket Number
        match_case = case_pattern.search(entry)
        if match_case:
            data["case_id"] = "JV " + match_case.group(1).strip() + " " + match_case.group(2).strip()
        else:
            data["case_id"] = ""

        match_docket = docket_pattern.search(entry)
        if match_docket:
            data["docket_number"] = match_docket.group(1).strip()
        else:
            data["docket_number"] = ""
        
        
        # 5) Defendant Name and 6) Defendant Type
        match_defendant = defendant_pattern.search(entry)
        if match_defendant:
            data["defendant_name"] = match_defendant.group(1).strip()
            data["defendant_type"] = match_defendant.group(2).strip()
        else:
            data["defendant_name"] = ""
            data["defendant_type"] = ""
        
        # 7) Judge
        match_judge = judge_pattern.search(entry)
        if match_judge:
            data["judge"] = match_judge.group(1).strip()
        else:
            data["judge"] = ""
        
        # 8) Classification
        match_classification = classification_pattern.search(entry)
        if match_classification:
            data["classification"] = match_classification.group(1).strip()
        else:
            data["defendant_type"] = ""
        
        # 9) Filed Date
        match_filed = filed_pattern.search(entry)
        if match_filed:
            data["filed_date"] = match_filed.group(1).strip()
        else:
            data["filed_date"] = ""
        
        # 10) Termination Date
        match_termination = termination_pattern.search(entry)
        if match_termination:
            data["termination_date"] = match_termination.group(1).strip()
        else:
            data["termination_date"] = ""
        
        results.append(data)
    
    return results


def parse_parties(blocks):
    """
    Given a list of party-information blocks (strings),
    return a list of lists. Each inner list corresponds
    to one block of text and contains party dictionaries.
    """

    # A helper regex to identify the start of a new Party + Status line.
    # e.g. "Juvenile ACTIVE", "Mom ACTIVE", "Guardian Ad Litem ACTIVE", etc.
    # Some lines might contain extra words (e.g. "Ryan J Baburek owes $68.00"),
    # so we can account for those patterns if needed.
    # For simplicity, let's capture lines that end with "ACTIVE" or "INACTIVE".
    party_header_pattern = re.compile(r'^\s*(.+?)\s+(ACTIVE|INACTIVE)\s*$', re.IGNORECASE)

    # For phone detection, we look for something resembling "402-xxx-xxxx".
    # If the attorney phone line is always in the right column, we can do
    # a quick check for that pattern in the attorney column.
    phone_pattern = re.compile(r'\b\d{3}-\d{3}-\d{4}\b')

    all_results = []

    for raw_text in blocks:
        lines = raw_text.splitlines()
        
        # Skip the first line if it’s the "Party Attorney" header or blank
        # You might also skip additional lines if needed
        while lines and ('Party' in lines[0] or not lines[0].strip()):
            lines.pop(0)
        
        parties = []
        current_party = None
        
        def start_new_party(line):
            """
            Given a line like "Juvenile ACTIVE", returns a party dict with role, status.
            """
            m = party_header_pattern.match(line)
            if not m:
                return None
            role = m.group(1).strip()
            status = m.group(2).strip()
            return {
                "role": role,
                "status": status,
                "name": "",
                "address_lines": [],
                "attorney_name": "",
                "attorney_address_lines": [],
                "attorney_phone": ""
            }

        for line in lines:
            # We'll split columns around ~column 40. Adjust as needed.
            left_col = line[:40].rstrip('\n')
            right_col = line[40:].rstrip('\n')

            # If this line starts a new party, push old one and create new.
            maybe_party = start_new_party(line)
            if maybe_party:
                # If we have a current party, store it
                if current_party:
                    parties.append(current_party)
                current_party = maybe_party
                continue

            # If not starting a new party, we are populating data for the current party.
            if not current_party:
                # It can happen if there's text before the first "Party" line
                # We'll just ignore that or handle specially.
                continue
            
            # Try to detect if this is the line that has "name on left" and "attorney name on right".
            # The simplest check: if both left_col and right_col are non-empty, treat them as
            # party name and attorney name (assuming the first time we see them).
            # If the party already has a name, then left_col lines might be addresses.
            # Same for attorney.
            left_str = left_col.strip()
            right_str = right_col.strip()

            if left_str and not current_party["name"]:
                # Assume the first non-empty left string is the party’s name
                current_party["name"] = left_str
                if right_str:
                    current_party["attorney_name"] = right_str
            elif left_str and current_party["name"] and not right_str:
                # Then it's probably a party address line
                current_party["address_lines"].append(left_str)
            elif left_str and current_party["name"] and right_str:
                # It's possible we are seeing some new line with both left & right content
                # Perhaps a second line of addresses for each side? 
                current_party["address_lines"].append(left_str)
                # or if attorney name is empty
                if not current_party["attorney_name"]:
                    current_party["attorney_name"] = right_str
                else:
                    # or it might be attorney address lines
                    current_party["attorney_address_lines"].append(right_str)
            else:
                # left_col is empty or near empty, right_col has data
                # or left_col has data but we already have a name, etc.
                if left_str:
                    # Additional lines for party address
                    current_party["address_lines"].append(left_str)
                if right_str:
                    # Could be attorney name if empty, else attorney address
                    if not current_party["attorney_name"]:
                        current_party["attorney_name"] = right_str
                    else:
                        # Possibly phone or address
                        phone_match = phone_pattern.search(right_str)
                        if phone_match:
                            current_party["attorney_phone"] = phone_match.group(0)
                        # Store the entire line in attorney address lines as well
                        current_party["attorney_address_lines"].append(right_str)

        # If the last party is not None, add it
        if current_party:
            parties.append(current_party)

        all_results.append(parties)

    return all_results

def parse_offenses(blocks):
    """
    Given a list of multiline strings (blocks) containing offense info, 
    return a list of offense-lists. Each entry in the final list 
    corresponds to one block of text (i.e., one case).
    """

    # A phrase that indicates the block is from a prior system, so we ignore it.
    prior_system_phrase = "This case has been converted from a prior system"

    # Regex to find the "Count / Charge / Offense Class" lines.
    #
    # Example line:
    #   01  Juvenile-truant                          ; 
    # or
    #   02  No valid registration-car/pickup/stepvan ; Class 3 Misdemeanor
    # We'll capture:
    #   group(1) = "01"
    #   group(2) = "Juvenile-truant"
    #   group(3) = "Class 3 Misdemeanor" or "" if missing
    #
    count_charge_pattern = re.compile(
        r'^\s*(\d{2})\s+(.*?)\s*;\s*(.*?)\s*$'
    )

    # Regex for lines like "Offense Date is 02/29/2016"
    offense_date_pattern = re.compile(r'Offense Date is\s+(\d{2}/\d{2}/\d{4})')

    # Regex for lines like "Plea is  Admit"
    plea_pattern = re.compile(r'Plea is\s+(.*)$', re.IGNORECASE)

    # Regex for lines like "Finding is"
    finding_pattern = re.compile(r'Finding is\s*(.*)$', re.IGNORECASE)

    # Regex for lines that start with "AMENDED TO..."
    # e.g. "AMENDED TO...Count dropped/dismissed ;"
    amended_pattern = re.compile(r'^AMENDED TO\.\.\.(.*)$', re.IGNORECASE)

    # Regex for lines that begin "Sentence includes:"
    sentence_includes_pattern = re.compile(r'Sentence includes:', re.IGNORECASE)

    # For each block, return a list of "offense" dictionaries:
    # { "count": "01", "charge": "...", "offense_class": "...", "offense_date": "...",
    #   "plea": "...", "finding": "...", "amended_to": "...", "sentences": [...] }
    all_cases = []

    for raw_text in blocks:
        # 1) Check for prior system phrase
        if prior_system_phrase in raw_text:
            # Skip entirely
            all_cases.append([])  # or you can skip appending altogether
            continue

        # 2) Split into lines
        lines = raw_text.splitlines()
        
        # Skip header lines up to the "Count  Charge  Offense Class" line
        # or if the line is empty. Some blocks have a standard line like:
        # "Count                 Charge                    Offense Class".
        # We'll drop everything until we find that line or run out of lines.
        while lines and "Count" in lines[0] and "Charge" in lines[0]:
            lines.pop(0)  # remove the header

        # We'll store offenses for this block
        offenses = []
        current_offense = None

        # A small helper to finalize the current offense and start a new one
        def start_new_offense(count_num, charge, offense_class):
            return {
                "count": count_num.strip(),
                "charge": charge.strip(),
                "offense_class": offense_class.strip(),
                "offense_date": "",
                "plea": "",
                "finding": "",
                "amended_to": "",
                "sentences": []  # list of textual lines describing each sentence item
            }

        # 3) Iterate lines
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            i += 1
            if not line.strip():
                # skip blank lines
                continue

            # Check if this line starts a new count
            m_count = count_charge_pattern.match(line)
            if m_count:
                # If we have a current offense, finalize it
                if current_offense:
                    offenses.append(current_offense)
                # Start a new offense
                count_num = m_count.group(1)
                charge_text = m_count.group(2)
                offense_class_text = m_count.group(3)
                current_offense = start_new_offense(count_num, charge_text, offense_class_text)
                continue

            # If not a new count line, it must be details for the current offense.
            if not current_offense:
                # There's a line that doesn't match a new offense but we have no current offense
                # -> we ignore or handle as needed
                continue

            # Attempt to match known patterns in detail lines
            # 1) Offense Date
            m_offense_date = offense_date_pattern.search(line)
            if m_offense_date:
                current_offense["offense_date"] = m_offense_date.group(1).strip()
                continue

            # 2) Plea
            m_plea = plea_pattern.search(line)
            if m_plea:
                # e.g. "Plea is  Admit"
                # or "Plea is  Plea Changed to Guilty"
                current_offense["plea"] = m_plea.group(1).strip()
                continue

            # 3) Finding
            m_finding = finding_pattern.search(line)
            if m_finding:
                current_offense["finding"] = m_finding.group(1).strip()
                continue

            # 4) Amended/Disposition
            m_amended = amended_pattern.match(line)
            if m_amended:
                # e.g. "AMENDED TO...Count dropped/dismissed"
                current_offense["amended_to"] = m_amended.group(1).strip()
                continue

            # 5) Sentences
            #    We look for "Sentence includes:"
            #    Then subsequent lines until we hit another known pattern or new count
            m_sentence = sentence_includes_pattern.search(line)
            if m_sentence:
                # gather sentence lines until we see a new count or block end or known pattern
                while i < len(lines):
                    peek_line = lines[i].rstrip()
                    
                    # If `peek_line` looks like a new count or is a known pattern line,
                    # we stop collecting sentences. We check if it matches our count regex.
                    if count_charge_pattern.match(peek_line):
                        break
                    if offense_date_pattern.search(peek_line):
                        break
                    if plea_pattern.search(peek_line):
                        break
                    if finding_pattern.search(peek_line):
                        break
                    if amended_pattern.match(peek_line):
                        break
                    if "Sentence includes:" in peek_line:
                        break

                    current_offense["sentences"].append(peek_line.strip())
                    i += 1
                continue
            
            # If we get here, it's either an unknown line or a sub-line of something else
            # Possibly partial sentencing info or a blank. We can optionally store it 
            # or ignore it. For demonstration, let’s check if it might be part of a sentence:
            if "Probation" in line or "Community Service" in line:
                # Possibly a line describing sentencing detail
                current_offense["sentences"].append(line.strip())
                continue

            # Otherwise ignore the line or store it as needed:
            # current_offense["sentences"].append(line.strip())
            # For now, let's ignore it.

        # End of lines: if we have a pending offense, store it
        if current_offense:
            offenses.append(current_offense)

        all_cases.append(offenses)

    return all_cases


def parse_events_from_pre(pre_text):
    """
    Given the raw text inside a <pre>...</pre> block,
    return a list of event dictionaries.
    Each event dictionary can have:
      - date (str)
      - event_type (str)
      - initiated_by (str) [optional if found]
      - description (list of lines)
      - links (list of href links found in the description)
    """

    # 1) Remove surrounding <pre>...</pre> if present, or just trust pre_text is only inside
    #    We'll just parse line by line.
    lines = pre_text.splitlines()

    # Regex to detect lines that begin an event, of the form:
    #   "MM/DD/YYYY <some event text>"
    # e.g. "07/24/1989 Return Filed"
    # We'll capture date in group(1) and event description in group(2).
    event_start_pattern = re.compile(r'^\s*(\d{2}/\d{2}/\d{4})\s+(.*)$')

    # A regex to find `href="..."`
    href_pattern = re.compile(r'href=\'(.*?)\'', re.IGNORECASE)

    events = []
    current_event = None

    # Helper to start a new event dictionary
    def start_new_event(evt_date, evt_type):
        return {
            "date": evt_date.strip(),
            "event_type": evt_type.strip(),
            "initiated_by": "",
            "description": [],
            "links": []
        }

    # We also look for lines like:
    #   "This action initiated by NAME"
    # within an event’s detail lines, and store that in `initiated_by`.
    initiated_by_pattern = re.compile(r'This action initiated by\s+(.*)$', re.IGNORECASE)

    for line in lines:
        line_stripped = line.rstrip()
        if not line_stripped:
            # skip empty or whitespace-only lines
            continue

        # Check if this line starts a new event
        match_event = event_start_pattern.match(line_stripped)
        if match_event:
            # If we had a current event in progress, store it first
            if current_event:
                events.append(current_event)
            # Start a new event
            evt_date = match_event.group(1)
            evt_type = match_event.group(2)
            current_event = start_new_event(evt_date, evt_type)
            continue

        # If we're in the middle of an event, let's accumulate details
        if current_event:
            # Check if line has "This action initiated by ..."
            match_initiated = initiated_by_pattern.search(line_stripped)
            if match_initiated:
                current_event["initiated_by"] = match_initiated.group(1).strip()

            # Check for any links in the line
            links_in_line = href_pattern.findall(line_stripped)
            # Add them to the event's links if found
            for link in links_in_line:
                current_event["links"].append(link.strip())

            # Add the raw line to the event's description
            current_event["description"].append(line_stripped)
        else:
            # If we encounter a line that doesn't match a date and we have no open event,
            # it's either preliminary text or we can ignore it. 
            # We'll ignore in this example.
            continue

    # End of lines: if there's a final event in progress, store it
    if current_event:
        events.append(current_event)

    return events
