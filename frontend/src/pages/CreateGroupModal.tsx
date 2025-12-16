import React, { useState } from 'react';
import './CreateGroupModal.css';

interface CreateGroupModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: (name: string) => void;
}

export default function CreateGroupModal({ visible, onClose, onSuccess }: CreateGroupModalProps) {
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  if (!visible) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('分组名称不能为空');
      return;
    }

    if (name.length > 20) {
      setError('分组名称不能超过20个字符');
      return;
    }

    onSuccess(name.trim());
    setName('');
    setError('');
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container">
        <div className="modal-header">
          <h3>新建分组</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="group-name">分组名称</label>
            <input
              type="text"
              id="group-name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              placeholder="请输入分组名称"
              maxLength={20}
            />
            {error && <div className="error-message">{error}</div>}
          </div>
          <div className="modal-actions">
            <button type="button" className="btn cancel" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="btn primary">
              确定
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
