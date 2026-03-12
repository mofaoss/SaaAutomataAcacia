
import os
import re

def find_strings():
    results = []
    # Patterns for _("...") and _('...')
    i18n_pattern = re.compile(r'_\(["\'](.*?)["\'](?:, msgid=["\'].*?["\'])?\)')
    # Patterns for description="..." and tips="..."
    decl_pattern = re.compile(r'(?:description|tips)\s*[:=]\s*(?:"{3}(.*?)"{3}|\'{3}(.*?)\'{3}|"(.*?)"|\'(.*?)\')', re.DOTALL)
    
    for root, dirs, files in os.walk('app/features'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find i18n strings
                    for match in i18n_pattern.finditer(content):
                        s = match.group(1)
                        if any(c.isalpha() for c in s): # Check if it contains letters (likely English)
                             results.append({'file': path, 'type': 'i18n', 'text': s, 'line': content.count('\n', 0, match.start()) + 1})
                    
                    # Find declaration strings
                    for match in decl_pattern.finditer(content):
                        s = next(g for g in match.groups() if g is not None)
                        if any(c.isalpha() for c in s):
                            results.append({'file': path, 'type': 'decl', 'text': s, 'line': content.count('\n', 0, match.start()) + 1})
                            
    return results

if __name__ == "__main__":
    findings = find_strings()
    for f in findings:
        print(f"{f['file']}:{f['line']} [{f['type']}] {f['text'][:100]}")
