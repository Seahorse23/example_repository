




workbook = openpyxl.load_workbook(output_file)
    for sheet_name in sheet_names:
        if sheet_name in workbook.sheetnames:  # Only modify sheets that were written
            sheet = workbook[sheet_name]
                # Add hyperlinks in the "Link" column
            for row in range(2, sheet.max_row + 1):  # Start at 2 (skip header row)
                cell = sheet[f"A{row}"]  # "Link" column corresponds to column A
                if cell.value:  # Ensure the cell is not empty
                    issue_key = cell.value
                    cell.value = issue_key  # This will be the displayed text
                    cell.hyperlink = f"https://sazka.atlassian.net/browse/{issue_key}"  # Add hyperlink
                    cell.style = "Hyperlink"
            for column in sheet.columns:
                max_length = 0
                column_letter = openpyxl.utils.get_column_letter(column[0].column)  # Get the column letter
                for cell in column:
                    try:
                        if cell.value:  # Ensure the cell has a value
                            max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass
                adjusted_width = max_length + 2  # Add padding for better readability
                sheet.column_dimensions[column_letter].width = adjusted_width
    
    # Save the modified workbook
    workbook.save(output_file)






def mailReport_new(data):
    smtp_server = config['email']['smtp_server']
    from_address = config['email']['from_address']

    arg = arguments()

    to_address = arg['to']
    cc_address = arg['cc']

    # Vytvoření MIME zprávy
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = ', '.join(to_address)
    msg['Cc'] = ', '.join(cc_address)
    msg['Subject'] = data['Subject']

    # Získání aktuálního času s časovou zónou
    timezone = pytz.timezone('Europe/Prague')
    current_time = datetime.now(timezone)
    msg['Date'] = current_time.strftime('%a, %d %b %Y %H:%M:%S %z')

    # Přidání HTML obsahu
    html_content = f"""
    <html>
      <body>
          {data['html']}
          <p>
          <small>Tento report byl vygenerovaný automaticky s pomocí AI, může tedy obsahovat chyby.</small>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    ### Updated XLSX-Handling Section
    for file_path in data['files']:
        if file_path.endswith('.xlsx'):  # Check if the file is an Excel file
            with open(file_path, 'rb') as file:
                attachment = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')  # MIME type for .xlsx
                attachment.set_payload(file.read())  # Read the file and set it as the payload

            # Encode the file as Base64
            encoders.encode_base64(attachment)

            # Add headers to the attachment
            attachment.add_header('Content-Disposition', 'attachment', filename=file_path.split('/')[-1])

            # Attach the file to the email
            msg.attach(attachment)

            # Delete the file after attaching
            os.remove(file_path)

    print(f"connecting to {smtp_server}...")
    # Připojení k SMTP serveru a odeslání e-mailu
    with smtplib.SMTP(smtp_server, 25, timeout=10) as server:
        # server.set_debuglevel(1)
        # server.starttls()
        # server.login(from_address, 'YourEmailPassword')  # Přidat heslo zde nebo v konfiguračním souboru
        server.send_message(msg)

    print("Email sent successfully!")

    return

























parsed_issues_data = [
            parsed_issues_current,  # Guaranteed
            parsed_issues_prev,     # Guaranteed
            parsed_issues_warning,  # Conditional (may be empty)
        ]
        sheet_names = [
            "Created last month",
            "Resolved last month",
            "! Open > 1 month !",
        ]
        # Export Parsed Issues to Excel
        excel_file = create_excel_file(parsed_issues_data, sheet_names)
    
        ##### Build HTML Email #####
        month = get_current_month()
        html = f"""
        Ahoj, <br>zasílám přehled incidentů IGT za poslední měsíc ({month} 2025).
        """
        html += f"<h2>Incidenty za reportovaný měsíc - celkem {len(parsed_issues_current)}</h2>"
        html += html_format_list_IGT(parsed_issues_current)
    
        html += f"<h2>Incidenty vytvořené v předchozích měsících a uzavřené v reportovaném měsíci - celkem {len(parsed_issues_prev)}</h2>"
        html += html_format_list_IGT(parsed_issues_prev)
    
        if parsed_issues_warning:
            html += f"<h2>Incidenty otevřené déle jak 1 měsíc - celkem {len(parsed_issues_warning)}</h2>"
            html += html_format_list_IGT(parsed_issues_warning)
    
        ##### Send Email #####
        email = {
            'Subject': f"IGT incidents - {month} 2025",
            'html': html,
            'files': [excel_file]  # Attach Excel file
        }
        mailReport(email)
    
    
    if __name__ == "__main__":
        main()
    







def create_excel_file(parsed_issues_data, sheet_names, output_file=None):
    """
    Saves multiple lists of parsed issues into an Excel file, only creating sheets for non-empty lists.

    Args:
        parsed_issues_data (list): A list of parsed issue lists (e.g., [list1, list2, list3]).
        sheet_names (list): Names of the sheets corresponding to the lists.
        output_file (str): Path to save the file (default: dynamically generated name).
    """
    # Dynamically set file name if not provided
    if output_file is None:
        prev_month = get_month()  # Call your existing function
        output_file = f"IGT_Excel_Report_{prev_month}_2025.xlsx"

    # Create an Excel file dynamically based on non-empty lists
    with pd.ExcelWriter(output_file) as writer:
        for issues_list, sheet_name in zip(parsed_issues_data, sheet_names):
            if issues_list:  # Only save non-empty lists
                rows = []  # Flatten list into rows for consistent keys
                for issue in issues_list:
                    rows.append({
                        "Link": f"https://sazka.atlassian.net/browse/{issue['key']}",
                        "Summary": issue['summary'],
                        "Type": issue['type'],
                        "Priority": issue['severity'],
                        "Status": issue['status'],
                        "Created": issue['created'],
                        "Updated": issue['updated'],
                        "Time to Resolution": issue.get('time_to_resolution', None),
                    })

                # Convert rows to DataFrame and write to the sheet
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel file saved: {output_file}")
    return output_file












def parse_issues_IGT(issues):
    parsed_issues = []
    
    # Init pro chart data
    stat={}

    #for issue in issues['issues']:
    for issue in issues:
        #if issue['fields']['customfield_11379'] is None:    # End Outage
        #    continue
        data={"key":issue['key']}
#        pprint(issue['key'])
        data['summary']=issue['fields']['summary']
        data['impact']=issue['fields']['customfield_11647']
        data['type']=issue['fields']['issuetype']['name']
        data['status']=issue['fields']['status']['name']
        data['priority']=issue['fields']['priority']['name']
        if issue['fields']['customfield_10444']:
            data['severity']=issue['fields']['customfield_10444']['value']
        else:
            data['severity']=None
        data['downtime']=issue['fields']['customfield_11405']
        data['minutes_down']=parse_downtime(data['downtime'])
        #pprint(data['downtime'])
        data['start']=issue['fields']['customfield_11378']

        if issue['fields']['customfield_11379'] is not None:
            data['end'] = issue['fields']['customfield_11379']
        else:
            data['end'] = datetime.now(timezone).strftime('%Y-%m-%dT%H:%M:%S.000%z')

        #data['end']=issue['fields']['customfield_11379']
        month = data['end'][:7] 
        
        created_raw = issue['fields']['created']
        dt_c = datetime.strptime(created_raw, '%Y-%m-%dT%H:%M:%S.%f%z')
        data['created'] = dt_c.strftime('%d/%m/%Y %H:%M') 

        updated_raw = issue['fields']['updated']
        dt_u= datetime.strptime(updated_raw, '%Y-%m-%dT%H:%M:%S.%f%z')
        data['updated'] = dt_u.strftime('%d/%m/%Y %H:%M') 
        
        data['time_to_resolution']=issue['fields']['customfield_10052']['completedCycles']['remainingTime']
        #pprint(data['end'])
# USERS:

        data['reporter']=issue['fields']['reporter'].get('displayName', None)
        data['reporter_email']=issue['fields']['reporter'].get('emailAddress', None)
        if issue['fields']['assignee']:
            data['assignee']=issue['fields']['assignee'].get('displayName', None)
            data['assignee_email']=issue['fields']['assignee'].get('emailAddress', None)
        else:
            data['assignee'] = None
            data['assignee_email'] = None


        # Vytvoření klíče z kombinace měsíce a priority
        key = (month, data['priority'])

        # Inicializace záznamu, pokud neexistuje
        if key not in stat:
            stat[key] = {
                'month': month,
                'severity': data['priority'],
                'incident_count': 1,
                'total_downtime': data['minutes_down']
            }
        else:
            # Aktualizace hodnot pro daný klíč
            stat[key]['incident_count'] += 1
            stat[key]['total_downtime'] += data['minutes_down']


        # Agregace dat během zpracování každého incidentu
        if data['origin_source'] is not None:
            for origin in data['origin_source']:
                cause_count[origin] += 1
                cause_downtime[origin] += data['minutes_down']

#Services stats:
        priority = data['priority'].lower()
        downtime = data['minutes_down']

        for service in data['services_affected']:
            service_name = service['Name']


            # Aktualizace statistiky služby
            service_stats[service_name]['name'] = service_name
            service_stats[service_name]['critical'] = service['Critical']
            service_stats[service_name]['downtime'][priority] += downtime
            service_stats[service_name]['count'][priority] += 1


        if data['services_crit'] == "<span style='color:red;'>Critical</span>":
            total_stats['downtime'][priority] += downtime
            total_stats['count'][priority] += 1


    out = {
        'issues':parsed_issues,
        'stat':stat, 
        'causes': {
            'cause_count':cause_count,
            'cause_downtime':cause_downtime
        },
        'services_stat':service_stats,
        'global_stat':total_stats
    }
    
    return out

def html_format_list_IGT(parsed_issues):
    
    html = """
    <table style='padding: 2px 8px;'>
    <tr><th align='left'>Link</th><th align='left'>Souhrn</th><th align='left'>Assignee</th><th align='left'>Vytvořeno</th></tr>
    """
    for issue in parsed_issues:
        #pprint(issue)
    

        jira_link = f"<a href='{config['jira']['server']}/browse/{issue['key']}'>{issue['key']}</a>"
        services_affected = ', '.join(service['Name'] for service in issue['services_affected'])

        html += f"""
        <tr>
            <td rowspan=2 style='vertical-align: top; padding: 8px; white-space: nowrap;'>{jira_link}</td>
            <td style='vertical-align: top;'><strong>{issue['summary']}</strong></td>
            <td style='vertical-align: top;'>{issue['type']}</td>
            <td style='vertical-align: top;'>{issue['assignee']}</td>
            <td style='vertical-align: top;'>{issue['severity']}</td>
            <td style='vertical-align: top;'>{issue['created']}</td>
            <td style='vertical-align: top;'>{issue['updated']}</td>
            <td style='vertical-align: top;'>{issue['time_to_resolution']}</td>
        </tr>

        <tr><td colspan=3><hr></td></tr>
        
        """
    


    html += "</table>"

    
    return html










        customfield_10052 = issue['fields'].get('customfield_10052', {})  # Fallback to empty dict
        completed_cycles = customfield_10052.get('completedCycles', [])  

        if completed_cycles:  # Ensure list is not empty
            data['time_to_resolution'] = completed_cycles[0]['remainingTime']['friendly']  # Extract the value
        else:
            data['time_to_resolution'] = "No completed cycles available"  # Handle empty lists
