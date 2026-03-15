// ── FreeCDN brand override ──────────────────────────────────────────────────
// 在 Vue 上下文挂载前，把后端注入的 GoEdge 品牌信息替换为 FreeCDN
;(function patchBrand() {
	// 替换 document.title 中的 GoEdge 字样
	var _titleDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'title');
	if (_titleDesc) {
		var _origTitleSet = _titleDesc.set;
		Object.defineProperty(document, 'title', {
			set: function(v) {
				_origTitleSet.call(this, typeof v === 'string' ? v.replace(/GoEdge/g, 'FreeCDN') : v);
			},
			get: _titleDesc.get,
			configurable: true
		});
	}
	document.title = document.title.replace(/GoEdge/g, 'FreeCDN');

	// ── 移除 settings 页面左侧子菜单中的「商业版本」链接 ─────────────────────
	// GoEdge 在 settings/* 页面里用模板固定写入了 authority 菜单项，需要用 DOM 删除
	function removeCommercialMenuItems() {
		var links = document.querySelectorAll('a[href]');
		links.forEach(function(a) {
			var href = a.getAttribute('href') || '';
			// 匹配 /settings/authority 及其子路径
			if (/\/settings\/authority/.test(href)) {
				var parent = a.parentElement;
				// 移除 <a> 本身或其 <li> 父节点
				if (parent && (parent.tagName === 'LI' || parent.tagName === 'DIV')) {
					parent.remove();
				} else {
					a.remove();
				}
			}
		});
	}

	// DOM 已就绪时执行；Vue 渲染后可能动态插入，监听 MutationObserver 兜底
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', removeCommercialMenuItems);
	} else {
		removeCommercialMenuItems();
	}
	// MutationObserver 兜底，确保 Vue 渲染后也能清除
	var _observer = new MutationObserver(function() {
		removeCommercialMenuItems();
	});
	document.addEventListener('DOMContentLoaded', function() {
		_observer.observe(document.body, { childList: true, subtree: true });
		// 3 秒后断开，避免长期监听影响性能
		setTimeout(function() { _observer.disconnect(); }, 3000);
	});
})();

Tea.context(function () {
	this.moreOptionsVisible = false
	this.globalMessageBadge = 0

	if (typeof this.leftMenuItemIsDisabled == "undefined") {
		this.leftMenuItemIsDisabled = false
	}

	// ── 过滤商业版菜单 & 替换品牌名 ──────────────────────────────────────────
	var COMMERCIAL_CODES = ['authority', 'ns', 'ad', 'business']
	if (Array.isArray(this.teaModules)) {
		this.teaModules = this.teaModules.filter(function(m) {
			return COMMERCIAL_CODES.indexOf(m.code) === -1
		})
	}
	// teaTitle / teaName 由后端注入，替换 GoEdge 字样
	if (typeof this.teaTitle === 'string') {
		this.teaTitle = this.teaTitle.replace(/GoEdge/gi, 'FreeCDN')
	}
	if (typeof this.teaName === 'string') {
		this.teaName = this.teaName.replace(/GoEdge/gi, 'FreeCDN')
	}

	// ── 屏蔽商业授权页面内容 ──────────────────────────────────────────────────
	if (window.location.pathname.indexOf('/settings/authority') === 0) {
		window.addEventListener('DOMContentLoaded', function() {
			var mainBox = document.querySelector('.main-box')
			if (mainBox) {
				mainBox.innerHTML = '<div class="ui message info" style="margin:2em"><i class="icon info circle"></i>此功能在 FreeCDN 中不可用。</div>'
			}
		})
	}

	this.$delay(function () {
		if (this.$refs.focus != null) {
			this.$refs.focus.focus()
		}

		if (!window.IS_POPUP) {
			// 检查消息
			this.checkMessages()

			// 检查集群节点同步
			this.loadNodeTasks();

			// 检查DNS同步
			this.loadDNSTasks()
		}
	})

	/**
	 * 切换模板
	 */
	this.changeTheme = function () {
		this.$post("/ui/theme")
			.success(function (resp) {
				teaweb.successToast("界面风格已切换")
				this.teaTheme = resp.data.theme
			})
	}

	/**
	 * 左侧子菜单
	 */
	this.showSubMenu = function (menu) {
		if (menu.alwaysActive) {
			return
		}
		if (this.teaSubMenus.menus != null && this.teaSubMenus.menus.length > 0) {
			this.teaSubMenus.menus.$each(function (k, v) {
				if (menu.id == v.id) {
					return
				}
				v.isActive = false
			})
		}
		menu.isActive = !menu.isActive
	};

	/**
	 * 检查消息
	 */
	this.checkMessages = function () {
		this.$post("/messages/badge")
			.params({})
			.success(function (resp) {
				this.globalMessageBadge = resp.data.count

				// add dot to title
				let dots = "••• "
				if (typeof document.title == "string") {
					if (resp.data.count > 0) {
						if (!document.title.startsWith(dots)) {
							document.title = dots + document.title
						}
					} else if (document.title.startsWith(dots)) {
						document.title = document.title.substring(dots.length)
					}
				}
			})
			.done(function () {
				let delay = 6000
				if (this.globalMessageBadge > 0) {
					delay = 30000
				}
				this.$delay(function () {
					this.checkMessages()
				}, delay)
			})
	}

	this.checkMessagesOnce = function () {
		this.$post("/messages/badge")
			.params({})
			.success(function (resp) {
				this.globalMessageBadge = resp.data.count
			})
	}

	this.showMessages = function () {
		teaweb.popup("/messages", {
			height: "28em",
			width: "50em"
		})
	}

	/**
	 * 底部伸展框
	 */
	this.showQQGroupQrcode = function () {
		teaweb.popup("/about/qq", {
			width: "21em",
			height: "30em"
		})
	}

	/**
	 * 弹窗中默认成功回调
	 */
	if (window.IS_POPUP === true) {
		this.success = window.NotifyPopup
	}

	/**
	 * 节点同步任务
	 */
	this.doingNodeTasks = {
		isDoing: false,
		hasError: false,
		isUpdated: false
	}

	this.loadNodeTasks = function () {
		if (!Tea.Vue.teaCheckNodeTasks) {
			return
		}
		let isStream = false
		this.$post("/clusters/tasks/check")
			.params({
				isDoing: this.doingNodeTasks.isDoing ? 1 : 0,
				hasError: this.doingNodeTasks.hasError ? 1 : 0,
				isUpdated: this.doingNodeTasks.isUpdated ? 1 : 0
			})
			.timeout(60)
			.success(function (resp) {
				this.doingNodeTasks.isDoing = resp.data.isDoing
				this.doingNodeTasks.hasError = resp.data.hasError
				this.doingNodeTasks.isUpdated = true
				isStream = resp.data.shouldWait
			})
			.done(function () {
				this.$delay(function () {
					this.loadNodeTasks()
				}, isStream ? 5000 : 30000)
			})
	}

	this.showNodeTasks = function () {
		teaweb.popup("/clusters/tasks/listPopup", {
			height: "28em",
			width: "54em"
		})
	}

	/**
	 * DNS同步任务
	 */
	this.doingDNSTasks = {
		isDoing: false,
		hasError: false,
		isUpdated: false
	}

	this.loadDNSTasks = function () {
		if (!Tea.Vue.teaCheckDNSTasks) {
			return
		}
		let isStream = false
		this.$post("/dns/tasks/check")
			.params({
				isDoing: this.doingDNSTasks.isDoing ? 1 : 0,
				hasError: this.doingDNSTasks.hasError ? 1 : 0,
				isUpdated: this.doingDNSTasks.isUpdated ? 1 : 0
			})
			.timeout(60)
			.success(function (resp) {
				this.doingDNSTasks.isDoing = resp.data.isDoing
				this.doingDNSTasks.hasError = resp.data.hasError
				this.doingDNSTasks.isUpdated = true
				isStream = resp.data.isStream
			})
			.done(function () {
				this.$delay(function () {
					this.loadDNSTasks()
				}, isStream ? 5000 : 30000)
			})
	}

	this.showDNSTasks = function () {
		teaweb.popup("/dns/tasks/listPopup", {
			height: "28em",
			width: "54em"
		})
	}

	this.LANG = function (code) {
		if (window.LANG_MESSAGES != null) {
			let message = window.LANG_MESSAGES[code]
			if (typeof message == "string") {
				return message
			}
		}
		if (window.LANG_MESSAGES_BASE != null) {
			let message = window.LANG_MESSAGES_BASE[code]
			if (typeof message == "string") {
				return message
			}
		}
		return "{{ LANG('" + code + "') }}"
	}

	this.switchLang = function () {
		this.$post("/settings/lang/switch")
			.success(function () {
				window.location.reload()
			})
	}
});

window.NotifySuccess = function (message, url, params) {
	if (typeof (url) == "string" && url.length > 0) {
		if (url[0] != "/") {
			url = Tea.url(url, params);
		}
	}
	return function () {
		teaweb.success(message, function () {
			window.location = url;
		});
	};
};

window.NotifyReloadSuccess = function (message) {
	return function () {
		teaweb.success(message, function () {
			window.location.reload()
		})
	}
}

window.NotifyDelete = function (message, url, params) {
	teaweb.confirm(message, function () {
		Tea.Vue.$post(url)
			.params(params)
			.refresh();
	});
};

window.NotifyPopup = function (resp) {
	window.parent.teaweb.popupFinish(resp);
};

window.ChangePageSize = function (size) {
	let url = window.location.toString();
	url = url.replace(/page=\d+/g, "page=1")
	if (url.indexOf("pageSize") > 0) {
		url = url.replace(/pageSize=\d+/g, "pageSize=" + size)
	} else {
		if (url.indexOf("?") > 0) {
			let anchorIndex = url.indexOf("#")
			if (anchorIndex < 0) {
				url += "&pageSize=" + size;
			} else {
				url = url.substring(0, anchorIndex) + "&pageSize=" + size + url.substr(anchorIndex);
			}
		} else {
			url += "?pageSize=" + size;
		}
	}
	window.location = url;
};