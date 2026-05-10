/**
 * ConfirmDialog — generic confirmation modal
 *
 * Props:
 *   open       — boolean, show/hide modal
 *   title      — modal title
 *   message    — confirmation message
 *   confirmLabel — confirmation button text (default: "Delete")
 *   onConfirm  — confirm callback
 *   onCancel   — cancel callback
 */
export default function ConfirmDialog({
                                          open,
                                          title = 'Are you sure?',
                                          message,
                                          confirmLabel = 'Delete',
                                          onConfirm,
                                          onCancel,
                                      }) {
    if (!open) return null;

    return (
        <div className="confirm-overlay" onClick={onCancel}>
            <div className="confirm-dialog" onClick={e => e.stopPropagation()}>
                <div className="confirm-header">
                    <span className="confirm-icon">⚠</span>
                    <h3 className="confirm-title">{title}</h3>
                </div>
                {message && (
                    <p className="confirm-message">{message}</p>
                )}
                <div className="confirm-actions">
                    <button className="btn btn-outline" onClick={onCancel}>
                        Cancel
                    </button>
                    <button className="btn btn-danger-solid" onClick={onConfirm}>
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}