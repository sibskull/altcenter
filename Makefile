
.PHONY: install

install:
	mkdir -p $(DESTDIR)/usr/share/altcenter/plugins
	cp -a plugins/*.py $(DESTDIR)/usr/share/altcenter/plugins
	mkdir -p $(DESTDIR)/usr/share/altcenter/translations
	cp -a translations/*.md $(DESTDIR)/usr/share/altcenter/translations
	cp -a *.py $(DESTDIR)/usr/share/altcenter
	cp altcenter_ru.qm $(DESTDIR)/usr/share/altcenter
	mkdir -p $(DESTDIR)/usr/share/altcenter/res
	install -Dpm0644 res/policies.json $(DESTDIR)/usr/share/altcenter/res/policies.json
	install -Dpm0755 altcenter $(DESTDIR)/usr/bin/altcenter
	install -Dpm0644 altcenter.desktop $(DESTDIR)/usr/share/applications/altcenter.desktop
	sed 's|^Exec=.*|& --at-startup|' altcenter.desktop > altcenter-autostart.desktop
	install -Dpm0644 altcenter-autostart.desktop $(DESTDIR)/etc/xdg/autostart/altcenter.desktop
