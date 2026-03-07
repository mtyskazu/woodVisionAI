/**
 * DataDisplay コンポーネント
 * 取得したデータの描画とエラー表示を担当する
 */
class DataDisplay {
    /**
     * @param {HTMLElement} containerEl - データ表示先のコンテナ要素
     */
    constructor(containerEl) {
        this._container = containerEl;
    }

    /**
     * データ一覧を描画する
     * @param {Array<{id: number, title: string, body: string}>} items
     */
    render(items) {
        if (!items || items.length === 0) {
            this._container.innerHTML = '<p class="placeholder-text">表示するデータがありません。</p>';
            return;
        }

        const fragment = document.createDocumentFragment();

        items.forEach((item) => {
            const div = document.createElement('div');
            div.className = 'data-item';

            const title = document.createElement('div');
            title.className = 'data-title';
            title.textContent = item.title;

            const body = document.createElement('div');
            body.className = 'data-body';
            body.textContent = item.body;

            div.appendChild(title);
            div.appendChild(body);
            fragment.appendChild(div);
        });

        this._container.innerHTML = '';
        this._container.appendChild(fragment);
    }

    /**
     * エラーメッセージを表示する
     * @param {string} message
     */
    renderError(message) {
        this._container.innerHTML = `<p class="error-message">${message}</p>`;
    }
}