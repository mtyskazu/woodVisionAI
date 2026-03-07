/**
 * UpdateButton コンポーネント
 * 更新ボタンの状態管理とローディング制御を担当する
 */
class UpdateButton {
    /**
     * @param {HTMLButtonElement} buttonEl - 更新ボタン要素
     * @param {HTMLElement} overlayEl - ローディングオーバーレイ要素
     */
    constructor(buttonEl, overlayEl) {
        this._button = buttonEl;
        this._overlay = overlayEl;
        this._isLoading = false;
    }

    /**
     * クリックイベントハンドラを登録する
     * @param {Function} handler - クリック時に実行されるコールバック
     */
    onClick(handler) {
        this._button.addEventListener('click', () => {
            if (!this._isLoading) {
                handler();
            }
        });
    }

    /**
     * ローディング状態を切り替える
     * @param {boolean} loading - true でローディング表示、false で非表示
     */
    setLoading(loading) {
        this._isLoading = loading;
        this._button.disabled = loading;

        if (loading) {
            this._overlay.classList.remove('hidden');
        } else {
            this._overlay.classList.add('hidden');
        }
    }
}