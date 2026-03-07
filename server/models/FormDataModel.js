const mongoose = require('mongoose');

const formDataSchema = new mongoose.Schema(
  {
    field1: {
      type: String,
      required: [true, 'field1 は必須です'],
      trim: true,
    },
    field2: {
      type: String,
      required: [true, 'field2 は必須です'],
      trim: true,
    },
  },
  {
    timestamps: { createdAt: 'createdAt', updatedAt: 'updatedAt' },
  }
);

module.exports = mongoose.model('FormData', formDataSchema);
