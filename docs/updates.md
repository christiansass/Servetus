---
layout: page
title: Updates
permalink: /updates/
---

{% for post in site.posts %}
### [{{ post.title }}]({{ post.url | relative_url }})
{{ post.date | date: "%B %-d, %Y" }} -- {{ post.author }}

{{ post.excerpt }}

---
{% endfor %}
