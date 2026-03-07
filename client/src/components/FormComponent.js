import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000/api/form';

function FormComponent() {
  const [formData, setFormData] = useState({ field1: '', field2: '' });
  const [savedData, setSavedData] = useState(null);
  const [savedId, setSavedId] = useState(null);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchSavedData = useCallback(async (id) => {
    try {
      const url = id
        ? `${API_BASE}/retrieve?id=${id}`
        : `${API_BASE}/retrieve`;
      const res = await fetch(url);
      const json = await res.json();
      if (json.success && json.data) {
        const { field1, field2, _id } = json.data;
        setSavedData({ field1, field2 });
        setSavedId(_id);
        return { field1, field2 };
      }
    } catch (err) {
      console.error('Retrieve error:', err);
    }
    return null;
  }, []);

  useEffect(() => {
    fetchSavedData();
  }, [fetchSavedData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus({ type: '', message: '' });

    try {
      const res = await fetch(`${API_BASE}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: savedId, ...formData }),
      });
      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.error || '保存に失敗しました');
      }

      const { field1, field2, _id } = json.data;
      setSavedData({ field1, field2 });
      setSavedId(_id);
      setStatus({ type: 'success', message: '保存しました' });
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (savedData) {
      setFormData({ ...savedData });
      setStatus({ type: 'info', message: '変更を元に戻しました' });
    } else {
      setFormData({ field1: '', field2: '' });
      setStatus({ type: 'info', message: 'フォームをリセットしました' });
    }
  };

  return (
    <div className="form-wrapper">
      <form onSubmit={handleSave} className="form-container">
        <div className="form-group">
          <label htmlFor="field1">入力内容 1</label>
          <input
            id="field1"
            name="field1"
            type="text"
            value={formData.field1}
            onChange={handleChange}
            placeholder="入力内容1を入力してください"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="field2">入力内容 2</label>
          <textarea
            id="field2"
            name="field2"
            value={formData.field2}
            onChange={handleChange}
            placeholder="入力内容2を入力してください"
            rows={4}
            required
          />
        </div>

        {status.message && (
          <div className={`status-message status-${status.type}`}>
            {status.message}
          </div>
        )}

        <div className="button-group">
          <button type="submit" className="btn btn-save" disabled={isSubmitting}>
            {isSubmitting ? '保存中...' : '保存'}
          </button>
          <button
            type="button"
            className="btn btn-cancel"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            キャンセル
          </button>
        </div>
      </form>
    </div>
  );
}

export default FormComponent;
