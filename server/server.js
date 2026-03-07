const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const formRoutes = require('./routes/formRoutes');

const app = express();
const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/woodVisionAI';

app.use(cors());
app.use(express.json());

app.use('/api/form', formRoutes);

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

mongoose
  .connect(MONGO_URI)
  .then(() => {
    console.log('MongoDB に接続しました');
    app.listen(PORT, () => {
      console.log(`サーバーがポート ${PORT} で起動しました`);
    });
  })
  .catch((err) => {
    console.error('MongoDB 接続エラー:', err);
    process.exit(1);
  });
