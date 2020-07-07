def on_correction(updates, original, **kwargs):
    sub = []
    if updates.get('subject'):
        for x in updates.get('subject'):
            if x['name'] != 'republish':
                sub.append(x)
        updates['subject'] = sub
    
def init_app(app):
    app.on_update_archive_correct += on_correction