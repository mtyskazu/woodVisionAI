/**
 * メインアプリケーションスクリプト
 * 更新ボタンのイベント連携とデータフロー制御を行う
 */
(function () {
    'use strict';

    const API_ENDPOINT = 'https://jsonplaceholder.typicode.com/posts?_limit=5';

    const dataContainer = document.getElementById('data-container');
    const updateButton = document.getElementById('update-button');
    const loadingOverlay = document.getElementById('loading-overlay');

    const dataDisplay = new DataDisplay(dataContainer);
    const updateBtn = new UpdateButton(updateButton, loadingOverlay);

    updateBtn.onClick(async () => {
        updateBtn.setLoading(true);

        try {
            const response = await fetch(API_ENDPOINT);
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            const data = await response.json();
            dataDisplay.render(data);
        } catch (error) {
            console.error('Error fetching data:', error);
            dataDisplay.renderError('データの取得に失敗しました。ネットワーク接続を確認してください。');
        } finally {
            updateBtn.setLoading(false);
        }
    });
})();