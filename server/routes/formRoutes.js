const express = require('express');
const router = express.Router();
const FormData = require('../models/FormDataModel');

/**
 * POST /api/form/save
 * フォームデータを保存する。id が含まれていれば更新、なければ新規作成。
 */
router.post('/save', async (req, res) => {
  try {
    const { id, field1, field2 } = req.body;

    let saved;
    if (id) {
      saved = await FormData.findByIdAndUpdate(
        id,
        { field1, field2 },
        { new: true, runValidators: true }
      );
      if (!saved) {
        return res.status(404).json({ error: '指定された ID のデータが見つかりません' });
      }
    } else {
      saved = await FormData.create({ field1, field2 });
    }

    res.json({ success: true, data: saved });
  } catch (err) {
    console.error('Save error:', err);
    res.status(500).json({ error: 'データの保存に失敗しました', details: err.message });
  }
});

/**
 * GET /api/form/retrieve
 * 最新の保存済みフォームデータを取得する。
 * クエリパラメータ id が指定されていれば、そのドキュメントを返す。
 */
router.get('/retrieve', async (req, res) => {
  try {
    const { id } = req.query;

    let data;
    if (id) {
      data = await FormData.findById(id);
      if (!data) {
        return res.status(404).json({ error: '指定された ID のデータが見つかりません' });
      }
    } else {
      data = await FormData.findOne().sort({ updatedAt: -1 });
    }

    res.json({ success: true, data: data || null });
  } catch (err) {
    console.error('Retrieve error:', err);
    res.status(500).json({ error: 'データの取得に失敗しました', details: err.message });
  }
});

module.exports = router;
