#!/usr/bin/env python3
"""Update LogisticsPage.tsx to use extracted dialog components."""
import shutil

path = "plugins/logistics/frontend/LogisticsPage.tsx"
backup_path = path + ".bak2"
shutil.copy2(path, backup_path)
print(f"Backup: {backup_path}")

with open(path) as f:
    lines = f.readlines()


# ── Find dialog blocks by state variable ──
def find_dialog_block(lines, state_var):
    """Find the block starting with <Dialog open={state_var and ending with </Dialog>."""
    start = None
    for i, line in enumerate(lines):
        stripped = line.replace(" ", "").replace("\n", "")
        if f'<Dialogopen={{{state_var}' in stripped:
            start = i
            break
    if start is None:
        for i, line in enumerate(lines):
            if '<Dialog' in line and f'open={{{state_var}' in ''.join(lines[i:i+8]).replace(' ', '').replace('\n', ''):
                start = i
                break
    if start is None:
        return None, None

    depth = 0
    in_block = False
    for j in range(start, len(lines)):
        l = lines[j]
        for k in range(len(l)):
            if (l[k:k+8] == '<Dialog ' or l[k:k+8] == '<Dialog\n' or l[k:k+10] == '<Dialog\n '):
                depth += 1
                in_block = True
        depth -= l.count('</Dialog>')
        if depth == 0 and in_block:
            return start, j
    return start, len(lines) - 1


comp_replacements = {
    "isDetailMenuOpen": '''      <DetailMenuDialog
        selectedCylinder={selectedCylinder}
        isDetailMenuOpen={isDetailMenuOpen}
        detailError={detailError}
        productById={productById}
        gasById={gasById}
        brandById={brandById}
        canUpdate={canUpdate}
        canMaintenance={canMaintenance}
        canTransition={canTransition}
        canRetimbrado={canRetimbrado}
        canServiceManage={canServiceManage}
        canLabelPrint={canLabelPrint}
        canScan={canScan}
        openEditDialog={openEditDialog}
        setIsHydrotestOpen={setIsHydrotestOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        setIsServiceOpen={setIsServiceOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        setIsScanOpen={setIsScanOpen}
        openViewSection={openViewSection}
        closeDetailContext={closeDetailContext}
        formatDate={formatDate}
      />
''',
    "isFullDetailOpen": '''      <FullDetailInfoDialog
        selectedCylinder={selectedCylinder}
        isFullDetailOpen={isFullDetailOpen}
        detailError={detailError}
        productById={productById}
        gasById={gasById}
        brandById={brandById}
        canUpdate={canUpdate}
        canMaintenance={canMaintenance}
        canTransition={canTransition}
        canRetimbrado={canRetimbrado}
        canServiceManage={canServiceManage}
        canLabelPrint={canLabelPrint}
        canScan={canScan}
        openEditDialog={openEditDialog}
        setIsHydrotestOpen={setIsHydrotestOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        setIsServiceOpen={setIsServiceOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        setIsScanOpen={setIsScanOpen}
        closeDetailContext={closeDetailContext}
        transitionsQuery={transitionsQuery}
        traceQuery={traceQuery}
        hydrotestsQuery={hydrotestsQuery}
        warrantiesQuery={warrantiesQuery}
        retimbradosQuery={retimbradosQuery}
        ownershipQuery={ownershipQuery}
        labelHistoryQuery={labelHistoryQuery}
        servicesQuery={servicesQuery}
        labelDataQuery={labelDataQuery}
        filteredScans={filteredScans}
        serviceTypeById={serviceTypeById}
        nextState={nextState}
        setNextState={setNextState}
        handleTransition={handleTransition}
        transitionMutation={transitionMutation}
        serviceStatusMutation={serviceStatusMutation}
        deleteServiceMutation={deleteServiceMutation}
        setConfirmDelete={setConfirmDelete}
        getCylinderStateLabel={getCylinderStateLabel}
        formatDate={formatDate}
        formatDateTime={formatDateTime}
      />
''',
    "isHydrotestOpen": '''      <HydrotestDialog
        isHydrotestOpen={isHydrotestOpen}
        setIsHydrotestOpen={setIsHydrotestOpen}
        hydrotestForm={hydrotestForm}
        setHydrotestForm={setHydrotestForm}
        handleHydrotest={handleHydrotest}
        hydrotestMutation={hydrotestMutation}
      />
''',
    "isWarrantyOpen": '''      <WarrantyDialog
        isWarrantyOpen={isWarrantyOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        warrantyForm={warrantyForm}
        setWarrantyForm={setWarrantyForm}
        handleWarranty={handleWarranty}
        warrantyMutation={warrantyMutation}
        setIsWarrantyCustomerSearchOpen={setIsWarrantyCustomerSearchOpen}
      />
''',
    "isRetimbradoOpen": '''      <RetimbradoDialog
        isRetimbradoOpen={isRetimbradoOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        retimbradoForm={retimbradoForm}
        setRetimbradoForm={setRetimbradoForm}
        handleRetimbrado={handleRetimbrado}
        retimbradoMutation={retimbradoMutation}
      />
''',
    "isServiceOpen": '''      <ServiceDialog
        isServiceOpen={isServiceOpen}
        setIsServiceOpen={setIsServiceOpen}
        serviceForm={serviceForm}
        setServiceForm={setServiceForm}
        handleService={handleService}
        serviceMutation={serviceMutation}
        serviceTypesQuery={serviceTypesQuery}
      />
''',
    "isPrintLabelOpen": '''      <PrintLabelDialog
        isPrintLabelOpen={isPrintLabelOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        printLabelForm={printLabelForm}
        setPrintLabelForm={setPrintLabelForm}
        handlePrintLabel={handlePrintLabel}
        printLabelMutation={printLabelMutation}
      />
''',
    "isTransitionOpen": '''      <TransitionDialog
        isTransitionOpen={isTransitionOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        nextState={nextState}
        setNextState={setNextState}
        handleTransition={handleTransition}
        transitionMutation={transitionMutation}
        transitionsQuery={transitionsQuery}
        getCylinderStateLabel={getCylinderStateLabel}
      />
''',
    "isScanOpen": '''      <ScanDialog
        isScanOpen={isScanOpen}
        setIsScanOpen={setIsScanOpen}
        scanForm={scanForm}
        setScanForm={setScanForm}
        handleScan={handleScan}
        scanMutation={scanMutation}
      />
''',
}


# Find all blocks (process bottom-up to keep indices valid)
blocks = []
for state_var, repl in comp_replacements.items():
    start, end = find_dialog_block(lines, state_var)
    if start is not None and end is not None:
        blocks.append((start, end, repl))
        print(f"  {repl.splitlines()[0].strip().replace('<', '').split()[0]}: lines {start+1}-{end+1}")
    else:
        print(f"  NOT FOUND: {state_var}")

blocks.sort(key=lambda x: x[0], reverse=True)

for start, end, replacement in blocks:
    # Remove the indentation from replacement to match the context
    lines[start:end+1] = [replacement]


# ── Add new imports after last import line ──
new_imports = [
    'import { DetailMenuDialog } from "./cylinders/dialogs/DetailMenuDialog";\n',
    'import { FullDetailInfoDialog } from "./cylinders/dialogs/FullDetailInfoDialog";\n',
    'import { HydrotestDialog } from "./cylinders/dialogs/HydrotestDialog";\n',
    'import { WarrantyDialog } from "./cylinders/dialogs/WarrantyDialog";\n',
    'import { RetimbradoDialog } from "./cylinders/dialogs/RetimbradoDialog";\n',
    'import { ServiceDialog } from "./cylinders/dialogs/ServiceDialog";\n',
    'import { PrintLabelDialog } from "./cylinders/dialogs/PrintLabelDialog";\n',
    'import { TransitionDialog } from "./cylinders/dialogs/TransitionDialog";\n',
    'import { ScanDialog } from "./cylinders/dialogs/ScanDialog";\n',
]

last_import = max(i for i, line in enumerate(lines) if line.startswith('import '))
for idx, imp in enumerate(new_imports):
    lines.insert(last_import + 1 + idx, imp)
last_import += len(new_imports)

print(f"\nImports inserted after line {last_import}")

# ── Remove unused imports ──
# Single-line imports to remove
remove_imports = [
    'import { DropdownMenu, type DropdownItem } from "../../../apps/web/src/shared/ui/dropdown-menu";\n',
    'import { Dialog } from "../../../apps/web/src/shared/ui/dialog";\n',
]

for ri in remove_imports:
    try:
        lines.remove(ri)
        print(f"  Removed: {ri.strip()[:60]}...")
    except ValueError:
        pass

# For multi-line import of formatters, we need to check if Field is still needed
# Field is used in the existing dialogs... wait, Field was used in the extracted
# dialogs, not in the main page. Let me check if Field is used in remaining code.
# Actually, InfoBlock and DataCard are imported from the same module.
# Let me check what's still used from that import:
# Line 79: import { toNullable, ... formatDate, formatDateTime, InfoBlock, DataCard, Field } from ...
# InfoBlock and DataCard are no longer used (extracted to FullDetailInfoDialog)
# Field is still used? No, all Field usage was in the extracted dialogs
# But toNullable, toNumberOrNull, toIntegerOrNull, formatDate, formatDateTime ARE still used
# So we keep the import but remove InfoBlock and DataCard from it

# Check what's still used from the formatters import
formatters_line_idx = None
for i, line in enumerate(lines):
    if 'formatDate' in line and 'formatters' in line:
        formatters_line_idx = i
        break

if formatters_line_idx is not None:
    # Remove InfoBlock, DataCard from the import
    old = lines[formatters_line_idx]
    new = old.replace(', InfoBlock', '').replace(', DataCard', '')
    if old != new:
        lines[formatters_line_idx] = new
        print(f"  Updated formatters import: removed InfoBlock, DataCard")

# ── Write result ──
with open(path, 'w') as f:
    f.writelines(lines)

print(f"\nDone! Wrote {path}")
print(f"Lines: original ~1421 → new {len(lines)}")

# Count function body
func_start = None
for i, line in enumerate(lines):
    if 'export function LogisticsPage()' in line:
        func_start = i
        break
if func_start:
    body_lines = sum(1 for l in lines[func_start:] if l.strip() and not l.startswith('import '))
    print(f"Function body (non-empty): ~{body_lines} lines")
