def parse_issues_IGT(issues):
    parsed_issues = []
    
    # Init pro chart data
    stat={}

    # Inicializace počitadla pro příčiny incidentů
    cause_count = Counter()
    cause_downtime = defaultdict(int)

    # Inicializace statistik pro služby
    service_stats = defaultdict(lambda: {
        "name": "",
        "critical": False,
        "downtime": {"critical": 0, "major": 0, "minor": 0},
        "count": {"critical": 0, "major": 0, "minor": 0},
    })
    total_stats = {
        "downtime": {"critical": 0, "major": 0, "minor": 0},
        "count": {"critical": 0, "major": 0, "minor": 0},
    }
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
        data['created']=issue['fields']['created']
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
# SERVICES:
        #pprint(issue['fields']['customfield_11382'])
#        data['services_affected'],data['services_crit'],data['emails']=services(issue['fields']['customfield_11382'])
        services_data = issue['fields'].get('customfield_11382', None)
        if services_data is not None:
            data['services_affected'], data['services_crit'], data['emails'] = services(services_data)
        else:
            data['services_affected'] = []
            data['services_crit'] = ""
            data['emails'] = {'BO': [], 'TO': []}  # Prázdné seznamy pro konzistenci



        data['timeline']=issue['fields'].get('customfield_11078', None)
        data['description']=issue['fields']['description']
        data['origin_source'] = (
            [item['value'] for item in  issue['fields']['customfield_11448']]
            if issue['fields']['customfield_11448'] is not None
            else None
        )
        data['solver_statement']=issue['fields']['customfield_11451']
        data['action_points']=issue['fields']['customfield_11452']
        data['manager_summary']=issue['fields']['customfield_11491']
        parsed_issues.append(data)


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
