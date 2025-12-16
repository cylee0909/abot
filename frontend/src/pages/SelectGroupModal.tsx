import React, { useState, useEffect } from 'react';
import { getGroups, addStockToGroup, createGroup, type Group } from '../api/groups';
import CreateGroupModal from './CreateGroupModal';
import './SelectGroupModal.css';

interface SelectGroupModalProps {
  visible: boolean;
  stockCode: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function SelectGroupModal({ visible, stockCode, onClose, onSuccess }: SelectGroupModalProps) {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  // 获取所有分组
  const fetchGroups = async () => {
    if (!visible) return;
    
    setLoading(true);
    setError('');
    try {
      const data = await getGroups();
      setGroups(data);
    } catch (err) {
      setError('获取分组失败，请重试');
      console.error('获取分组失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, [visible]);

  if (!visible) return null;

  const handleSubmit = async () => {
    if (!selectedGroupId) {
      setError('请选择一个分组');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await addStockToGroup(selectedGroupId, stockCode);
      onSuccess?.();
      onClose();
    } catch (err) {
      setError('添加到分组失败，请重试');
      console.error('添加到分组失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (name: string) => {
    try {
      // 直接创建分组，而不是只刷新列表
      await createGroup(name);
      // 创建成功后刷新分组列表
      await fetchGroups();
    } catch (err: any) {
      console.error('创建分组失败:', err);
      // 检查是否是重复分组名称错误
      if (err.message?.includes('409') || err.message?.includes('unique') || err.message?.includes('duplicate')) {
        setError('分组名称已存在，请使用其他名称');
      } else {
        setError('创建分组失败，请重试');
      }
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container select-group-modal">
        <div className="modal-header">
          <h3>选择分组</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        <div className="modal-content">
          {error && <div className="error-message">{error}</div>}
          
          {loading ? (
            <div className="loading">加载中...</div>
          ) : (
            <div className="group-list">
              {/* 新建分组选项，作为第一个Item */}
              <div 
                className="group-item create-group"
                onClick={() => setIsCreateModalVisible(true)}
              >
                <div className="group-name">新建分组</div>
              </div>
              
              {groups.length === 0 ? (
                <div className="empty-groups">
                  <p>暂无分组</p>
                </div>
              ) : (
                groups.map((group) => (
                  <div 
                    key={group.id} 
                    className={`group-item ${selectedGroupId === group.id ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedGroupId(group.id);
                      setError('');
                    }}
                  >
                    <div className="group-name">{group.name}</div>
                    <div className="group-date">
                      {new Date(group.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button type="button" className="btn cancel" onClick={onClose}>
            取消
          </button>
          <button 
            type="button" 
            className="btn primary"
            onClick={handleSubmit}
            disabled={loading || !selectedGroupId}
          >
            {loading ? '处理中...' : '确定'}
          </button>
        </div>
      </div>
      
      {/* 新建分组弹窗 */}
      <CreateGroupModal 
        visible={isCreateModalVisible}
        onClose={() => setIsCreateModalVisible(false)}
        onSuccess={handleCreateGroup}
      />
    </div>
  );
}
