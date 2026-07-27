---
name: frontend-ui-identity
description: UI consistency, formularios, labels, botones, errores, dialogos, frontend patterns. Use when building or editing any frontend form, dialog, or page in any plugin — ensures visual consistency with the rest of the system.
---

# Frontend UI Identity

Use this skill when creating or editing any UI in the frontend: forms, dialogs, pages, or components.

Typical triggers:
- "crear formulario de..."
- "agregar campo a..."
- "modal para..."
- "componente visual para..."
- "se siente distinto a los otros modulos"

## Core rules

**Every new UI must feel native to the system. Zero invention of visual patterns.**

1. **Labels**: `<label className="block space-y-2 text-sm text-foreground"><span>Label</span>...children...</label>`. Never `text-xs`, never `text-muted-foreground` for labels.
2. **No red asterisks `*`**: the system has no required-field indicators anywhere. Backend validation is the enforcement.
3. **Buttons**: use `<Button>` from `shared/ui/button`, never raw `<button>` with inline styles. Variants: `"primary"` (default) and `"secondary"`.
4. **Errors**: use `<Alert title="Error">` from `shared/ui/alert`. Never raw red divs.
5. **Textarea**: use `<Textarea>` from `shared/ui/textarea`. Never raw `<textarea>`.
6. **Form spacing**: `space-y-4` inside CardContent, `space-y-6` for form-level sections.
7. **Button row**: `<div className="flex justify-end gap-3">` with Cancel (secondary) left, Save (primary) right.
8. **Section boxes**: `<div className="rounded-md border border-border p-4">` with `<p className="mb-3 text-sm font-medium text-foreground">` heading.
9. **Dialogs**: use `<Dialog>` from `shared/ui/dialog`. Standard structure: `<form className="space-y-6">` → `<Alert>` (if error) → sections → button row.
10. **No inline styles**: use Tailwind classes and shared UI components exclusively. No `style={{}}`, no hardcoded colors.
11. **Before creating**: check how CRM (`ModalNuevoCliente.tsx`), Stock, or Logistics forms do it. Imitate the pattern exactly.

## Component sources (always import from here)

| Need | Use |
|------|-----|
| Buttons | `shared/ui/button` → `Button` |
| Text inputs | `shared/ui/input` → `Input` |
| Textarea | `shared/ui/input` → `Textarea` (re-exported) |
| Searchable select | `shared/ui/combobox` → `Combobox` |
| Simple select | `shared/ui/select` → `Select` |
| Modal | `shared/ui/dialog` → `Dialog` |
| Error message | `shared/ui/alert` → `Alert` |
| Checkbox | `shared/ui/input` → `Checkbox` (re-exported) |
| Card sections | `shared/ui/card` → `Card, CardHeader, CardTitle, CardContent` |

## Quick checklist before finishing any UI

- [ ] Labels use `block space-y-2 text-sm text-foreground`
- [ ] No red asterisks
- [ ] Buttons imported from `shared/ui/button`
- [ ] Errors use `Alert`, not raw divs
- [ ] Spacing matches existing forms
- [ ] No raw HTML inputs (use `Input`, `Textarea`, etc.)
- [ ] No inline styles or hardcoded colors
