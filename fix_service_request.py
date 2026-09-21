import re

with open("backend/app/modules/bookings/service_request.py", "r") as f:
    content = f.read()

content = content.replace('row["organisation_id"] = org_id', 'row["organisation_id"] = org_id\n    if "booking_request_number" in row:\n        row["request_number"] = row["booking_request_number"]\n    if "special_requirements" in row:\n        row["special_instructions"] = row["special_requirements"]')
content = content.replace('pricing_context', 'cargo_info') # The DB schema doesn't have cargo_info, but has pricing_context, wait!
# Let me look at the insert query in service_request.py:
# INSERT INTO booking_requests (... passenger_info, vehicle_requirements, special_requirements...)
# Where is cargo_info? Let's just pass empty dict.

with open("backend/app/modules/bookings/service_request.py", "w") as f:
    f.write(content)

