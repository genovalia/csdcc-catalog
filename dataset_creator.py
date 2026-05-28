import json
import os
import glob
import shutil
import questionary
from typing import List, Dict, Any

def get_existing_values(field_path: str) -> List[Dict[str, Any]]:
    """Extract unique values for a specific field from all dcat.json files."""
    values = []
    seen = set()

    for dcat_file in glob.glob("**/dcat.json", recursive=True):
        if "templates" in dcat_file:
            continue
        try:
            with open(dcat_file, "r") as f:
                data = json.load(f)
                
            # Basic path traversal (e.g., "dcterms:publisher")
            parts = field_path.split('.')
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = None
                    break
            
            if current:
                # Use a string representation to detect duplicates
                str_val = json.dumps(current, sort_keys=True)
                if str_val not in seen:
                    values.append(current)
                    seen.add(str_val)
        except Exception:
            continue
    return values

def prompt_complex_field(field_name: str, field_path: str, display_attr: str) -> Dict[str, Any]:
    """Prompt for a complex field, offering existing values or a new entry."""
    existing = get_existing_values(field_path)
    
    choices = []
    for val in existing:
        label = val.get(display_attr, str(val))
        choices.append(questionary.Choice(title=label, value=val))
    
    choices.append(questionary.Choice(title="[Enter new...]", value="NEW"))
    
    result = questionary.select(
        f"Select {field_name}:",
        choices=choices
    ).ask()
    
    if result == "NEW":
        # This part should be customized based on the field structure
        # For simplicity in this helper, we'll handle the common ones here or specialize
        return None 
    return result

def create_dataset(
    dataset_id: str,
    title: str,
    description: str,
    publisher: Dict[str, Any],
    contact: Dict[str, Any],
    keywords: List[str],
    creator: Dict[str, Any],
    attributions: List[Dict[str, Any]],
    theme_name_en: str,
    theme_name_fr: str,
    identifier: str = "",
    theme_url: str = "",
    spatial: str = "",
    year_start: str = "",
    year_end: str = ""
):
    """Core logic to create dataset files and update catalog.json."""
    if os.path.exists(dataset_id):
        print(f"Directory {dataset_id} already exists. Skipping.")
        return

    # 3. Create Files
    os.makedirs(dataset_id)
    
    # Load template dcat
    with open("templates/dcat.jsonc", "r") as f:
        content = f.read()
        
    # Remove single line comments (start of line or after space)
    import re
    content = re.sub(r"^\s*//.*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s+//.*", "", content)
    dcat = json.loads(content)

    # Update template with values
    dcat["dcterms:title"] = title
    dcat["dcterms:description"] = description
    dcat["dcterms:publisher"] = publisher
    dcat["dcat:contactPoint"] = contact
    dcat["dcat:keyword"] = keywords
    dcat["dcterms:creator"] = creator
    dcat["prov:qualifiedAttribution"] = attributions
    dcat["dcterms:identifier"] = identifier
    dcat["dcat:theme"] = theme_url
    dcat["dcterms:spatial"] = spatial
    dcat["dcterms:temporal"]["time:hasBeginning"]["time:inXSDgYear"] = year_start
    dcat["dcterms:temporal"]["time:hasEnd"]["time:inXSDgYear"] = year_end

    # Write dcat.json
    with open(os.path.join(dataset_id, "dcat.json"), "w") as f:
        json.dump(dcat, f, indent=2)

    # Copy mapper and oca
    shutil.copy("templates/mapper.jsonc", os.path.join(dataset_id, "mapper.json"))
    shutil.copy("templates/oca.json", os.path.join(dataset_id, "oca.json"))
    
    # Update mapper ID and themes
    with open(os.path.join(dataset_id, "mapper.json"), "r") as f:
        mapper_content = f.read()
    mapper_content = mapper_content.replace("TEMPLATE_ID", dataset_id)
    mapper_content = mapper_content.replace("TEMPLATE_THEME_EN", theme_name_en)
    mapper_content = mapper_content.replace("TEMPLATE_THEME_FR", theme_name_fr)
    with open(os.path.join(dataset_id, "mapper.json"), "w") as f:
        f.write(mapper_content)

    # 4. Update catalog.json
    with open("catalog.json", "r") as f:
        catalog = json.load(f)
    
    catalog["content"].append({
        "id": dataset_id,
        "mapper": f"{dataset_id}/mapper.json",
        "OCA": f"{dataset_id}/oca.json",
        "DCAT": f"{dataset_id}/dcat.json"
    })
    
    with open("catalog.json", "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"Successfully created dataset '{dataset_id}'")

def create_dataset_interactive():
    # 1. Dataset ID
    dataset_id_raw = questionary.text("Dataset ID (e.g., bostau2):").ask()
    if not dataset_id_raw:
        print("Dataset ID is required.")
        return
    
    dataset_id = dataset_id_raw.replace("-", "")

    if os.path.exists(dataset_id):
        print(f"Directory {dataset_id} already exists.")
        return

    # 2. Metadata Collection
    title = questionary.text("Title:").ask()
    description = questionary.text("Description:").ask()
    
    # Publisher
    publishers = get_existing_values("dcterms:publisher")
    pub_choices = [questionary.Choice(title=p.get("foaf:name", str(p)), value=p) for p in publishers]
    pub_choices.append(questionary.Choice(title="[Enter new...]", value="NEW"))
    publisher = questionary.select("Publisher:", choices=pub_choices).ask()
    if publisher == "NEW":
        publisher = {
            "@id": questionary.text("Publisher ID (URL):", default="https://csdcc.ca/").ask(),
            "@type": "foaf:Organization",
            "foaf:name": questionary.text("Publisher Name:", default="CSDCC").ask(),
            "foaf:homepage": questionary.text("Publisher Homepage:", default="https://csdcc.ca/").ask()
        }

    # Contact Point
    contacts = get_existing_values("dcat:contactPoint")
    con_choices = [questionary.Choice(title=c.get("vcard:fn", str(c)), value=c) for c in contacts]
    con_choices.append(questionary.Choice(title="[Enter new...]", value="NEW"))
    contact = questionary.select("Contact Point:", choices=con_choices).ask()
    if contact == "NEW":
        contact = {
            "@type": "vcard:Kind",
            "vcard:fn": questionary.text("Contact Name:", default="CSDCC").ask(),
            "vcard:hasEmail": {
                "@id": f"mailto:{questionary.text('Contact Email:', default='csdcc.ca').ask()}"
            }
        }

    # Keywords
    keywords_raw = questionary.text("Keywords (comma separated):").ask()
    keywords = [k.strip() for k in keywords_raw.split(",")] if keywords_raw else []

    # Creator (Organization)
    creators_list = get_existing_values("dcterms:creator")
    organizations_flat = []
    seen_orgs = set()
    for c in creators_list:
        if isinstance(c, dict) and c.get("@type") == "foaf:Organization":
            s = json.dumps(c, sort_keys=True)
            if s not in seen_orgs:
                organizations_flat.append(c)
                seen_orgs.add(s)

    org_choices = [questionary.Choice(title=c.get("foaf:name", str(c)), value=c) for c in organizations_flat]
    org_choices.append(questionary.Choice(title="[Enter new...]", value="NEW"))
    creator = questionary.select("Lead Organization (Creator):", choices=org_choices).ask()
    if creator == "NEW":
        creator = {
            "@id": questionary.text("Organization ID (URL):").ask(),
            "@type": "foaf:Organization",
            "foaf:name": questionary.text("Organization Name:").ask(),
            "foaf:homepage": questionary.text("Organization Homepage:").ask()
        }

    # Qualified Attribution (People)
    attributions = []
    while questionary.confirm("Add an individual contributor (Qualified Attribution)?").ask():
        # Suggest existing people
        existing_attributions = get_existing_values("prov:qualifiedAttribution")
        people_flat = []
        seen_people = set()
        for attr_list in existing_attributions:
            if isinstance(attr_list, list):
                for attr in attr_list:
                    agent = attr.get("prov:agent")
                    if agent:
                        s = json.dumps(agent, sort_keys=True)
                        if s not in seen_people:
                            people_flat.append(agent)
                            seen_people.add(s)
        
        person_choices = [questionary.Choice(title=p.get("foaf:name", str(p)), value=p) for p in people_flat]
        person_choices.append(questionary.Choice(title="[Enter new...]", value="NEW"))
        person = questionary.select("Select Person:", choices=person_choices).ask()
        
        if person == "NEW":
            person = {
                "@id": questionary.text("Person ID (e.g. ORCID):").ask(),
                "@type": "foaf:Person",
                "foaf:name": questionary.text("Person Name:").ask()
            }
        
        role = questionary.text("Role (e.g. principalInvestigator):", default="principalInvestigator").ask()
        
        attributions.append({
            "@type": "prov:Attribution",
            "prov:agent": person,
            "dcat:hadRole": role
        })
    
    # 3. Create Files
    os.makedirs(dataset_id)
    
    # Theme name for mapper
    theme_name_en = questionary.text("Theme Name (English, e.g. Crop Rotation):").ask()
    theme_name_fr = questionary.text("Theme Name (French, e.g. Rotation des cultures):").ask()

    identifier = questionary.text("Identifier (e.g. DOI):").ask() or ""
    theme_url = questionary.text("Theme (URL):").ask() or ""
    spatial = questionary.text("Spatial (GeoNames URL):").ask() or ""
    year_start = questionary.text("Year Start:").ask()
    year_end = questionary.text("Year End:").ask()

    create_dataset(
        dataset_id=dataset_id,
        title=title,
        description=description,
        publisher=publisher,
        contact=contact,
        keywords=keywords,
        creator=creator,
        attributions=attributions,
        theme_name_en=theme_name_en,
        theme_name_fr=theme_name_fr,
        identifier=identifier,
        theme_url=theme_url,
        spatial=spatial,
        year_start=year_start,
        year_end=year_end
    )
