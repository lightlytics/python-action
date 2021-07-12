import json

from pulumi_aws import route53

from utils import get_route53_record_name_by_convention


def create_lightlytics_com_route53_zone_and_records():
    # Note: SOA and NS records are auto created
    lightlytics_com_zone = route53.Zone(
        "lightlytics_domain",
        name="lightlytics.com",
    )
    created_route53_records = []

    with open('./lightlytics_com_domains.json') as f:
        records_json = json.load(f)
        records_list = records_json.get("ResourceRecordSets")
        for record_data in records_list:
            record_name = record_data['Name']
            record_type = record_data['Type']
            record_ttl = record_data.get('TTL', 300)
            record_values = [value['Value'].replace('"', '') for value in record_data['ResourceRecords']]
            resource_name, _ = get_route53_record_name_by_convention(record_name, record_type)
            route53_record = route53.Record(
                resource_name,
                zone_id=lightlytics_com_zone.zone_id,
                name=record_name,
                type=record_type,
                ttl=record_ttl,
                records=record_values
            )
            created_route53_records.append(route53_record)
        return {"records": created_route53_records, "zone": lightlytics_com_zone}
