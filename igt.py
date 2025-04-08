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
