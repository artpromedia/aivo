"""
CLI tools for i18n string extraction and management.

Command-line tools for extracting translatable strings and managing locales.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import click
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po
import polib


def extract_js_strings(file_path: Path) -> Set[str]:
    """Extract translatable strings from JavaScript/TypeScript files."""
    patterns = [
        r't\([\'"`]([^\'"`]+)[\'"`]\)',  # t('string')
        r'i18n\.t\([\'"`]([^\'"`]+)[\'"`]\)',  # i18n.t('string')
        r'translate\([\'"`]([^\'"`]+)[\'"`]\)',  # translate('string')
        r'_\([\'"`]([^\'"`]+)[\'"`]\)',  # _('string')
    ]
    
    strings = set()
    content = file_path.read_text(encoding='utf-8')
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        strings.update(matches)
    
    return strings


def extract_python_strings(file_path: Path) -> Set[str]:
    """Extract translatable strings from Python files."""
    patterns = [
        r'_\([\'"]([^\'"]+)[\'"]\)',  # _('string')
        r'gettext\([\'"]([^\'"]+)[\'"]\)',  # gettext('string')
        r'ngettext\([\'"]([^\'"]+)[\'"]',  # ngettext('string'
        r'translate\([\'"]([^\'"]+)[\'"]\)',  # translate('string')
    ]
    
    strings = set()
    content = file_path.read_text(encoding='utf-8')
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        strings.update(matches)
    
    return strings


def extract_html_strings(file_path: Path) -> Set[str]:
    """Extract translatable strings from HTML/template files."""
    patterns = [
        r'\{\{\s*[\'"]([^\'"]+)[\'"]\s*\|\s*translate\s*\}\}',  # {{ 'string' | translate }}
        r'data-i18n=[\'"]([^\'"]+)[\'"]',  # data-i18n="string"
        r'i18n-key=[\'"]([^\'"]+)[\'"]',  # i18n-key="string"
        r'\$t\([\'"]([^\'"]+)[\'"]\)',  # $t('string')
    ]
    
    strings = set()
    content = file_path.read_text(encoding='utf-8')
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        strings.update(matches)
    
    return strings


def scan_directory(directory: Path, extensions: List[str]) -> Dict[str, Set[str]]:
    """Scan directory for translatable strings."""
    results = {}
    
    for ext in extensions:
        pattern = f"**/*.{ext}"
        files = list(directory.glob(pattern))
        
        for file_path in files:
            # Skip node_modules, .git, and other irrelevant directories
            if any(skip in str(file_path) for skip in [
                'node_modules', '.git', 'dist', 'build', '__pycache__'
            ]):
                continue
            
            try:
                if ext in ['js', 'ts', 'jsx', 'tsx']:
                    strings = extract_js_strings(file_path)
                elif ext in ['py']:
                    strings = extract_python_strings(file_path)
                elif ext in ['html', 'htm', 'vue', 'svelte']:
                    strings = extract_html_strings(file_path)
                else:
                    continue
                
                if strings:
                    results[str(file_path)] = strings
            except Exception as e:
                click.echo(f"Error processing {file_path}: {e}")
    
    return results


def create_pot_file(strings: Set[str], output_path: Path) -> None:
    """Create POT (Portable Object Template) file."""
    catalog = Catalog(
        project="AIVO i18n",
        version="1.0.0",
        copyright_holder="AIVO",
        charset="utf-8"
    )
    
    for string in sorted(strings):
        catalog.add(string)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        write_po(f, catalog)


def update_po_file(pot_path: Path, po_path: Path, locale: str) -> None:
    """Update existing PO file or create new one."""
    pot_file = polib.pofile(str(pot_path))
    
    if po_path.exists():
        # Update existing PO file
        po_file = polib.pofile(str(po_path))
        po_file.merge(pot_file)
    else:
        # Create new PO file
        po_file = polib.POFile()
        po_file.metadata = {
            'Project-Id-Version': 'AIVO i18n 1.0.0',
            'Language': locale,
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }
        
        for entry in pot_file:
            po_file.append(entry)
    
    po_path.parent.mkdir(parents=True, exist_ok=True)
    po_file.save(str(po_path))


def compile_po_to_json(po_path: Path, json_path: Path) -> None:
    """Compile PO file to JSON for web usage."""
    po_file = polib.pofile(str(po_path))
    translations = {}
    
    for entry in po_file:
        if entry.msgstr:  # Only include translated entries
            translations[entry.msgid] = entry.msgstr
    
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)


@click.group()
def cli():
    """AIVO i18n CLI tools."""
    pass


@cli.command()
@click.option('--source', '-s', default='..', help='Source directory to scan')
@click.option('--output', '-o', default='locales/messages.pot', help='Output POT file')
@click.option('--extensions', '-e', default='js,ts,py,html,vue', help='File extensions')
def extract(source: str, output: str, extensions: str):
    """Extract translatable strings from source files."""
    source_path = Path(source).resolve()
    output_path = Path(output)
    ext_list = [ext.strip() for ext in extensions.split(',')]
    
    click.echo(f"Scanning {source_path} for extensions: {ext_list}")
    
    # Scan for strings
    results = scan_directory(source_path, ext_list)
    
    # Collect all unique strings
    all_strings = set()
    file_count = 0
    
    for file_path, strings in results.items():
        all_strings.update(strings)
        file_count += 1
        click.echo(f"Found {len(strings)} strings in {file_path}")
    
    # Create POT file
    create_pot_file(all_strings, output_path)
    
    click.echo(f" Extracted {len(all_strings)} strings from {file_count} files")
    click.echo(f"   Created: {output_path}")


@cli.command()
@click.option('--pot', '-p', default='locales/messages.pot', help='POT template file')
@click.option('--locale', '-l', required=True, help='Target locale (e.g., en-US)')
@click.option('--output-dir', '-o', default='locales', help='Output directory')
def update_locale(pot: str, locale: str, output_dir: str):
    """Update or create PO file for specific locale."""
    pot_path = Path(pot)
    output_path = Path(output_dir) / locale / 'messages.po'
    
    if not pot_path.exists():
        click.echo(f" POT file not found: {pot_path}")
        return
    
    update_po_file(pot_path, output_path, locale)
    
    click.echo(f" Updated locale {locale}")
    click.echo(f"   File: {output_path}")


@cli.command()
@click.option('--locale', '-l', help='Specific locale to compile (all if not specified)')
@click.option('--input-dir', '-i', default='locales', help='Input directory with PO files')
@click.option('--output-dir', '-o', default='public/locales', help='Output directory for JSON')
def compile_translations(locale: str, input_dir: str, output_dir: str):
    """Compile PO files to JSON for web usage."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if locale:
        # Compile specific locale
        po_file = input_path / locale / 'messages.po'
        json_file = output_path / f'{locale}.json'
        
        if po_file.exists():
            compile_po_to_json(po_file, json_file)
            click.echo(f" Compiled {locale}")
        else:
            click.echo(f" PO file not found: {po_file}")
    else:
        # Compile all locales
        compiled_count = 0
        
        for locale_dir in input_path.iterdir():
            if locale_dir.is_dir():
                po_file = locale_dir / 'messages.po'
                json_file = output_path / f'{locale_dir.name}.json'
                
                if po_file.exists():
                    compile_po_to_json(po_file, json_file)
                    compiled_count += 1
                    click.echo(f" Compiled {locale_dir.name}")
        
        click.echo(f" Compiled {compiled_count} locales")


@cli.command()
@click.option('--locale', '-l', required=True, help='Locale to validate')
@click.option('--input-dir', '-i', default='locales', help='Input directory')
def validate_locale(locale: str, input_dir: str):
    """Validate PO file for completeness and issues."""
    po_path = Path(input_dir) / locale / 'messages.po'
    
    if not po_path.exists():
        click.echo(f" PO file not found: {po_path}")
        return
    
    po_file = polib.pofile(str(po_path))
    
    total_entries = len(po_file)
    translated_entries = len([e for e in po_file if e.msgstr])
    untranslated_entries = len(po_file.untranslated_entries())
    fuzzy_entries = len(po_file.fuzzy_entries())
    
    completion_rate = (translated_entries / total_entries) * 100 if total_entries > 0 else 0
    
    click.echo(f" Validation Report for {locale}")
    click.echo(f"   Total entries: {total_entries}")
    click.echo(f"   Translated: {translated_entries}")
    click.echo(f"   Untranslated: {untranslated_entries}")
    click.echo(f"   Fuzzy: {fuzzy_entries}")
    click.echo(f"   Completion: {completion_rate:.1f}%")
    
    if completion_rate >= 95:
        click.echo(" Locale is ready for production")
    elif completion_rate >= 80:
        click.echo("  Locale needs more translations")
    else:
        click.echo(" Locale is not ready for production")


@cli.command()
@click.option('--input-dir', '-i', default='locales', help='Input directory')
def stats(input_dir: str):
    """Show translation statistics for all locales."""
    input_path = Path(input_dir)
    
    click.echo(" Translation Statistics")
    click.echo("=" * 50)
    
    total_locales = 0
    
    for locale_dir in sorted(input_path.iterdir()):
        if locale_dir.is_dir():
            po_file = locale_dir / 'messages.po'
            
            if po_file.exists():
                po = polib.pofile(str(po_file))
                total = len(po)
                translated = len([e for e in po if e.msgstr])
                completion = (translated / total) * 100 if total > 0 else 0
                
                status = "" if completion >= 95 else "" if completion >= 80 else ""
                
                click.echo(f"{status} {locale_dir.name:10} {completion:6.1f}% ({translated:4}/{total:4})")
                total_locales += 1
    
    click.echo("=" * 50)
    click.echo(f"Total locales: {total_locales}")


if __name__ == '__main__':
    cli()
