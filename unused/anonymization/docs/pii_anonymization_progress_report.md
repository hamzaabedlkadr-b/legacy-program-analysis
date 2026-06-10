# PII Detection and Anonymization Progress Report

Date: 2026-05-18

## Objective

The goal is to identify and anonymize or pseudonymize personal data that may appear inside COBOL source files, copybooks, comments, display messages, string literals, and generated artifacts.

The main PII categories currently in scope are:

- Person names and surnames
- IBAN values
- Email addresses
- Italian codice fiscale values
- COBOL fields that may carry personal data, such as `NOME`, `COGNOME`, `MATRICOLA`, `CODDIP`, and `IBAN`

## Tools and Components Used

### Microsoft Presidio

Microsoft Presidio is used as the main PII detection engine.

It provides built-in recognizers for structured PII, including:

- `EMAIL_ADDRESS`
- `IBAN_CODE`
- `IT_FISCAL_CODE`
- `PHONE_NUMBER`
- `PERSON`
- `LOCATION`

Presidio is installed locally and can run offline after installation.

### spaCy Italian Model

The installed spaCy model is:

- `it_core_news_sm`

This model is used by Presidio for natural-language entity recognition, especially `PERSON` and `LOCATION`.

### Custom COBOL Recognizers

Because COBOL source code is very different from normal prose, custom recognizers were added in:

`unused/anonymization/scripts/scan_pii_presidio.py`

The current custom entities are:

- `COBOL_NAME_LITERAL`
- `COBOL_KEY_VALUE_NAME`
- `COBOL_COMMENT_NAME`
- `COBOL_PII_FIELD`
- `IBAN_LIKE`
- `WATCHLIST_PERSON`

These extend Presidio with COBOL-aware logic.

## Scripts Created

### PII Scanner

File:

`unused/anonymization/scripts/scan_pii_presidio.py`

Purpose:

- Scans files or folders for PII
- Uses Microsoft Presidio
- Adds COBOL-specific detection rules
- Outputs:
  - JSON findings
  - HTML visual report

Example command:

```powershell
python unused/anonymization/scripts/scan_pii_presidio.py unused/anonymization/artifacts/demo_pii/FAKE_FILE.CBL --out-dir unused/anonymization/artifacts/demo_pii/fake_file_report --entities PERSON IBAN_CODE IBAN_LIKE EMAIL_ADDRESS IT_FISCAL_CODE COBOL_NAME_LITERAL COBOL_KEY_VALUE_NAME COBOL_COMMENT_NAME
```

### Pseudonymization Script

File:

`unused/anonymization/scripts/pseudonymize_pii.py`

Purpose:

- Replaces detected structured PII with deterministic fake values
- Keeps referential consistency using a secret salt
- Supports:
  - IBAN-like pseudonyms
  - codice fiscale-like pseudonyms
  - labeled name fields such as `NOME=...` and `COGNOME=...`
  - COBOL name literals moved into name fields

Example command:

```powershell
python unused/anonymization/scripts/pseudonymize_pii.py unused/anonymization/artifacts/demo_pii/PDCBVC_fake_pii.CBL --out-dir unused/anonymization/artifacts/demo_pii/pseudonymized --salt demo-salt
```

## Test Files Created or Used

### Synthetic COBOL PII Demo

File:

`unused/anonymization/artifacts/demo_pii/PDCBVC_fake_pii.CBL`

Purpose:

- Fake COBOL file derived from the structure of `PDCBVC.CBL`
- Contains fake names, IBANs, codice fiscale values, and email examples
- Used to validate basic detection and pseudonymization behavior

### Additional Synthetic Stress Test

File:

`unused/anonymization/artifacts/demo_pii/FAKE_FILE.CBL`

Purpose:

- Contains many uppercase Italian names in comments, display messages, file names, and literals
- Used to test difficult name-detection cases
- Demonstrated that Microsoft Presidio alone is not enough for uppercase COBOL comments/messages

### Real COBOL Test File

File:

`temp/PDHASI06.CBL`

Purpose:

- Used to test the scanner on a more realistic COBOL source file
- The scan found PII-related fields, but no clear embedded IBAN, email, or codice fiscale values
- The name `Mattarella` appeared in a comment and required special handling

## Current Findings

### Structured PII Detection

Structured identifiers are detected well.

Strong detection categories:

- Email
- Valid IBAN
- IBAN-shaped values through `IBAN_LIKE`
- Italian codice fiscale

This is the most reliable part of the current solution.

### Person Name Detection

Person-name detection is more difficult.

Microsoft Presidio with spaCy can detect normal person names, but COBOL introduces challenges:

- Names may appear fully uppercase
- Names may appear as single surnames
- Names may appear inside comments
- Names may appear inside `DISPLAY`, `VALUE`, `STRING`, or file assignment literals
- COBOL program names and technical identifiers may look like names

Because of this, custom COBOL detection was added.

### COBOL Comment and Message Detection

The custom entity `COBOL_COMMENT_NAME` was added to detect possible names in:

- COBOL comments
- `DISPLAY` messages
- `VALUE` string literals
- `STRING` statements
- `ASSIGN TO` file names

This mode is intentionally optional because it is more aggressive and may produce false positives in some real COBOL files.

### Watchlist Handling

The entity `WATCHLIST_PERSON` was added for known names or surnames that must always be detected.

Watchlist file:

`unused/anonymization/artifacts/pii_watchlist/names.txt`

Current example:

```text
Mattarella
```

This is useful for known high-risk terms, but it is not a scalable replacement for general name detection.

## Important Limitations

### Microsoft Presidio Is Not Perfect for Names

Presidio is strong for structured data but weaker for names in legacy code.

Examples:

- It may miss isolated surnames such as `Mattarella`
- It may miss uppercase names in COBOL comments
- It may incorrectly classify COBOL identifiers as `PERSON` or `LOCATION`

### Watchlists Do Not Scale Alone

A watchlist is useful for known names, but it is not realistic to maintain every possible name or surname.

The better approach is to combine:

- Presidio
- COBOL-aware rules
- Context-based comment/message detection
- Optional watchlists for known sensitive names
- Manual review of HTML reports

### Automatic Rewriting Requires Care

Detection and pseudonymization should be separated.

The recommended process is:

1. Detect PII
2. Review the HTML report
3. Decide which entity types should be anonymized
4. Pseudonymize copied/exported artifacts
5. Re-scan the pseudonymized output

The original source files should not be modified directly without review.

## Current Recommended Detection Modes

### Strict Values-Only Scan

Use this mode when looking for clear values with fewer false positives:

```powershell
python unused/anonymization/scripts/scan_pii_presidio.py <input-file-or-folder> --out-dir <report-folder> --entities PERSON IBAN_CODE IBAN_LIKE EMAIL_ADDRESS IT_FISCAL_CODE COBOL_NAME_LITERAL COBOL_KEY_VALUE_NAME
```

### Aggressive Comment and Message Scan

Use this mode when names may appear in comments, display messages, or string literals:

```powershell
python unused/anonymization/scripts/scan_pii_presidio.py <input-file-or-folder> --out-dir <report-folder> --entities PERSON IBAN_CODE IBAN_LIKE EMAIL_ADDRESS IT_FISCAL_CODE COBOL_NAME_LITERAL COBOL_KEY_VALUE_NAME COBOL_COMMENT_NAME
```

### PII Field Risk Scan

Use this mode when identifying programs that process personal data fields:

```powershell
python unused/anonymization/scripts/scan_pii_presidio.py <input-file-or-folder> --out-dir <report-folder> --entities COBOL_PII_FIELD
```

## Next Steps

The next phase is to test different anonymization approaches and compare their accuracy and safety.

### Approach 1: Structured PII Pseudonymization

Target:

- IBAN
- Email
- Codice fiscale

Method:

- Use deterministic pseudonym generation
- Preserve format where useful
- Use a stable salt for consistent replacement

Expected result:

- High accuracy
- Low risk of breaking COBOL syntax

### Approach 2: COBOL Field-Based Name Pseudonymization

Target:

- `NOME`
- `COGNOME`
- `NOMINATIVO`
- `OPER-NOME`
- `NOME-REF`

Method:

- Replace values only when the COBOL field context clearly indicates a name
- Examples:
  - `MOVE 'Mario Rossi' TO TWCOB-NOME`
  - `05 WS-NOME PIC X(30) VALUE 'Mario Rossi'`

Expected result:

- Good precision
- Safer than replacing every detected `PERSON`

### Approach 3: Comment and Message Name Anonymization

Target:

- Names in comments
- Names in display messages
- Names in string literals

Method:

- Use `COBOL_COMMENT_NAME`
- Apply more conservative replacement rules
- Review HTML report before applying changes

Expected result:

- Better coverage of hidden names
- Higher false-positive risk

### Approach 4: Watchlist-Based Replacement

Target:

- Known sensitive names or surnames

Method:

- Maintain `unused/anonymization/artifacts/pii_watchlist/names.txt`
- Replace exact matches only

Expected result:

- Very high precision for known terms
- Not sufficient as a standalone solution

## Overall Assessment

The current solution is a practical first version for COBOL PII discovery.

Strengths:

- Good detection for IBAN, email, and codice fiscale
- COBOL-aware scanning is now available
- HTML reports make review easier
- Different scan modes allow strict or aggressive detection
- Runs locally after installation

Weaknesses:

- Name detection remains the hardest part
- Aggressive comment scanning can produce false positives
- Automatic anonymization of comments and free text requires review

Recommended position:

Use this as a detection and review pipeline first, then apply pseudonymization in controlled modes. The safest production workflow is to pseudonymize copied artifacts, not original source files, and always re-scan the output.


