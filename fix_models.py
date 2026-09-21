import os
import re

modules = [
    "invoices", "expenses", "payables", "billing", "trips", 
    "vehicles", "pl", "customers", "compliance", "drivers",
    "payments", "vendors"
]

base_dir = "backend/app/modules"

for mod in modules:
    model_path = os.path.join(base_dir, mod, "models.py")
    if not os.path.exists(model_path):
        continue
    
    with open(model_path, "r") as f:
        content = f.read()

    # Extract enums
    enums = []
    lines = content.split('\n')
    in_enum = False
    current_enum = []
    
    for line in lines:
        if "class" in line and "enum.Enum" in line:
            in_enum = True
            current_enum.append(line)
        elif in_enum:
            current_enum.append(line)
            if not line.strip() and len(current_enum) > 2: # heuristic to find end of enum
                enums.append('\n'.join(current_enum))
                in_enum = False
                current_enum = []
    
    if in_enum and current_enum:
         enums.append('\n'.join(current_enum))
    
    # Write enums.py
    if enums:
        with open(os.path.join(base_dir, mod, "enums.py"), "w") as f:
            f.write("import enum\n\n")
            f.write("\n".join(enums))
            
    # Delete models.py
    os.remove(model_path)
    print(f"Processed {mod}")

