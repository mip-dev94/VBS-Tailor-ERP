FROM odoo:19.0

USER root

# Copy custom addons
COPY ./vbs_planning /mnt/extra-addons/vbs_planning

# Fix permissions
RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
