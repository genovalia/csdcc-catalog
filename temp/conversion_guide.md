# CSV to DCAT Conversion Guide

This document outlines the procedure for converting rows from the `schema_metadata 1.csv` file into the DCAT-AP 3.0.1 compliant catalog structure.

## 1. Input Data Specs
- **File:** `temp/schema_metadata 1.csv`
- **Delimiter:** Semicolon (`;`)
- **Encoding:** UTF-8 with BOM (`utf-8-sig`)
- **Headers:** Contains duplicate headers for `attribution` and `theme`. Use a reader that handles duplicates by appending indices (e.g., `attribution_1`).

## 2. Directory Structure
For each row, create a directory named after the `nom_schema` value (removing the `.json` extension).
Example: `activate_1.json` -> folder `activate_1/`.

## 3. Field Mapping (CSV -> dcat.json)

| DCAT Field | CSV Column / Logic | Notes |
| :--- | :--- | :--- |
| `@id` | `https://csdcc.ca/catalog/{id}` | Base URL + directory name |
| `dcterms:identifier` | `nom_schema` (no ext) | Unique ID |
| `dcterms:title` | `titre` | |
| `dcterms:description` | `description` | |
| `dcterms:language` | `langue` | Default to "en" |
| `dcat:landingPage` | Extracted from `createur` | Look for the first URL in the string |
| `dcterms:publisher` | Default: CSDCC | `@id` and `foaf:homepage` left empty |
| `dcat:contactPoint` | `createur` (name part) | `vcard:fn` is the first part before comma |
| `dcat:keyword` | `mots_clefs` | Split by comma, strip spaces, ignore "NA" |
| `dcat:theme` | `theme` | Take the first non-NA value from `theme` columns |
| `dcterms:temporal` | `info_temporelle` | Split `YYYY-YYYY` into start and end years |
| `dcterms:spatial` | `info_spatiale` | |
| `dcterms:accessRights` | `droits_accès` | Map "RESTREINT" to RestrictedAccess URI |
| `dcterms:creator` | `attribution` columns | Parse name and ORCID URI if available |

## 4. Mapper Configuration (mapper.json)
- Use `templates/mapper.jsonc` as a base.
- **English Block (`en`):**
    - Populate `theme` and `spatial` as `literal` values.
    - Other fields use `jsonpath` or `jsonpath_multiple` to pull from `dcat.json`.
- **French Block (`fr`):**
    - Copy English `titre` and `description` to French literals as placeholders.
    - Populate `theme` and `spatial` literals.

## 5. Metadata Files
- **dcat.json:** The core metadata.
- **mapper.json:** The API mapping file.
- **oca.json:** Empty object `{}` (required by the API).

## 6. Catalog Update
Append the new dataset entry to the `content` array in the root `catalog.json` file.
