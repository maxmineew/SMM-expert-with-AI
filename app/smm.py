from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from generators.gigachat_client import GigaChatAuthError, GigaChatError
from app.models import User
from app import db
from generators.text_gen import PostGenerator
from generators.image_gen import ImageGenerator
from social_publishers.vk_publisher import VKPublisher, VKGroupAuthError, VKPublisherError
from social_stats.vk_stats import VKStats
from config import vk_api_key as default_vk_api_key, vk_group_id as default_vk_group_id


smm_bp = Blueprint('smm', __name__)


@smm_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')


@smm_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.vk_api_id = request.form['vk_api_id']
        user.vk_group_id = request.form['vk_group_id']
        db.session.commit()
        flash('Settings saved!', 'success')

    return render_template('settings.html', user=user)


@smm_bp.route('/post-generator', methods=['GET', 'POST'])
def post_generator():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        tone = request.form['tone']
        topic = request.form['topic']
        generate_image = 'generate_image' in request.form
        auto_post = 'auto_post' in request.form

        user = User.query.get(session['user_id'])
        vk_token = user.vk_api_id or default_vk_api_key
        vk_group = user.vk_group_id or default_vk_group_id

        try:
            post_gen = PostGenerator(tone, topic)
            post_content = post_gen.generate_post()

            image_url = None
            if generate_image:
                image_gen = ImageGenerator()
                image_prompt = post_gen.generate_post_image_description()
                image_url = image_gen.generate_image(image_prompt)

            if auto_post:
                if not vk_token or not vk_group:
                    flash('Укажите VK API ID и VK Group ID в Settings.', 'danger')
                    return render_template(
                        'post_generator.html',
                        post_content=post_content,
                        image_url=image_url,
                    )

                vk_publisher = VKPublisher(vk_token, vk_group)
                vk_image_url = image_url
                if image_url and image_url.startswith('/'):
                    vk_image_url = request.host_url.rstrip('/') + image_url

                try:
                    vk_publisher.publish_post(post_content, vk_image_url)
                    flash('Post published to VK successfully!', 'success')
                except VKGroupAuthError:
                    if vk_image_url:
                        vk_publisher.publish_post(post_content, None)
                        flash(
                            'Пост опубликован без фото. Ключ сообщества не поддерживает загрузку '
                            'изображений — для автопоста с фото нужен пользовательский токен '
                            '(получите по ссылке Kate Mobile из инструкции).',
                            'warning',
                        )
                    else:
                        raise

            return render_template('post_generator.html', post_content=post_content, image_url=image_url)
        except GigaChatAuthError:
            flash('Ошибка авторизации GigaChat. Проверьте gigachat_credentials в config.py.', 'danger')
        except GigaChatError as exc:
            flash(f'Ошибка GigaChat: {exc}', 'danger')
        except VKGroupAuthError as exc:
            flash(str(exc), 'danger')
        except VKPublisherError as exc:
            flash(f'Ошибка VK: {exc}', 'danger')
        except Exception as exc:
            flash(f'Не удалось сгенерировать контент: {exc}', 'danger')

    return render_template('post_generator.html')


@smm_bp.route('/vk-stats', methods=['GET'])
def vk_stats():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])

    vk_stats = VKStats(user.vk_api_id, user.vk_group_id)
    followers_count = vk_stats.get_followers()

    stats = {
        "Followers": followers_count,
        "Likes": "N/A",
        "Comments": "N/A",
        "Shares": "N/A"
    }

    return render_template('vk_stats.html', stats=stats)
