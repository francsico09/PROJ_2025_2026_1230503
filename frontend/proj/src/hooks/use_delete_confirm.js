import { useState } from 'react';

/**
 * A custom hook to manage delete confirmation state and actions.
 *
 * @param removeFn
 * @param onSuccess
 * @returns {{deleteTarget: unknown, deleting: boolean, handleDeleteClick: handleDeleteClick, handleDeleteConfirm: (function(): Promise<void>)|*, handleDeleteCancel: function(): void}}
 */
export function useDeleteConfirm(removeFn, onSuccess) {
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleting, setDeleting]         = useState(false);

    const handleDeleteClick = (...args) => {
        if (args.length === 1) {
            setDeleteTarget(args[0]);

        } else {
            const [e, item] = args;
            e?.stopPropagation();
            setDeleteTarget(item);
        }
    };

    const handleDeleteConfirm = async () => {
        if (!deleteTarget) return;
        setDeleting(true);
        try {
            await removeFn(deleteTarget.id);
            setDeleteTarget(null);
            onSuccess?.();
        } finally {
            setDeleting(false);
        }
    };

    const handleDeleteCancel = () => setDeleteTarget(null);

    return {
        deleteTarget,
        deleting,
        handleDeleteClick,
        handleDeleteConfirm,
        handleDeleteCancel,
    };
}