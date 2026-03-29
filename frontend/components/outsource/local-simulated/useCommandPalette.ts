import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import type { CommandPaletteAction } from './types';

export function useCommandPalette(actions: CommandPaletteAction[]) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredActions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return actions;
    }

    return actions.filter((action) =>
      `${action.label} ${action.hint}`.toLowerCase().includes(normalized)
    );
  }, [actions, query]);

  const runAction = useCallback((action: CommandPaletteAction) => {
    action.run();
    setIsOpen(false);
    setQuery('');
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setIsOpen((previous) => !previous);
      }

      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setTimeout(() => inputRef.current?.focus(), 0);
  }, [isOpen]);

  return {
    isOpen,
    setIsOpen,
    query,
    setQuery,
    inputRef,
    filteredActions,
    runAction,
  };
}
