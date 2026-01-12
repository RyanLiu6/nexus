# Sure (Finance) Troubleshooting

## Common Issues

### Sure Not Starting

**Symptoms**: Container exits immediately

**Solutions**:
1. Check logs: `docker logs sure-web -f`
2. Verify database is healthy: `docker ps | grep sure-db`
3. Check Redis is running: `docker ps | grep sure-redis`
4. Verify database credentials in `.env`

### Database Connection Failed

**Symptoms**: "Connection refused" or database errors

**Solutions**:
1. Check database container: `docker logs sure-db`
2. Verify database credentials in `.env`
3. Ensure network connectivity between containers
4. Check if database is ready: `docker exec sure-db pg_isready`

### OpenAI API Not Working

**Symptoms**: AI features not functioning

**Solutions**:
1. Verify API key in `.env`
2. Check API key validity
3. Check OpenAI account status
4. Review Sure logs for API errors

## Useful Commands

```bash
# View Sure logs
docker logs sure-web -f

# View worker logs
docker logs sure-worker -f

# View database logs
docker logs sure-db -f

# Restart Sure
docker restart sure-web sure-worker

# Access Sure database shell
docker exec -it sure-db psql -U sure_user -d sure_production

# Run Rails console
docker exec -it sure-web bundle exec rails console
```

## Configuration Files

- `services/sure/docker-compose.yml` - Container configuration
- `$NEXUS_ROOT_DIRECTORY/services/sure/storage/` - Sure data and uploads
- `.env` - Database and API credentials

## Database Management

### Check Database Status
```bash
docker exec -it sure-db psql -U sure_user -d sure_production -c "\dt"
```

### Backup Database
```bash
docker exec sure-db pg_dump -U sure_user sure_production > sure-backup.sql
```

### Restore Database
```bash
cat sure-backup.sql | docker exec -i sure-db psql -U sure_user -d sure_production
```

### Migrate Database
```bash
# Inside container
docker exec -it sure-web bundle exec rails db:migrate
```

## Troubleshooting Rails Issues

### Asset Precompilation Failed
```bash
docker exec -it sure-web bundle exec rails assets:precompile
```

### Run Database Migrations
```bash
docker exec -it sure-web bundle exec rails db:migrate
```

### Seed Database
```bash
docker exec -it sure-web bundle exec rails db:seed
```

## Performance Tuning

### Increase Worker Processes
```yaml
# In docker-compose.yml
services:
  sure-worker:
    command: bundle exec sidekiq -c 5 -q default
```

### Database Connection Pool
```yaml
# In .env or config
RAILS_MAX_THREADS=5
```

## Backup & Restore

### Backup Sure
```bash
# Backup database
docker exec sure-db pg_dump -U sure_user sure_production > sure-db-backup.sql

# Backup data
tar -czf sure-backup.tar.gz $NEXUS_ROOT_DIRECTORY/services/sure/storage/

# Save backup
mv sure-backup.tar.gz $NEXUS_BACKUP_DIRECTORY/
mv sure-db-backup.sql $NEXUS_BACKUP_DIRECTORY/
```

### Restore Sure
```bash
# Restore database
cat sure-db-backup.sql | docker exec -i sure-db psql -U sure_user -d sure_production

# Restore data
tar -xzf sure-backup.tar.gz -C $NEXUS_ROOT_DIRECTORY/services/sure/

# Restart containers
docker restart sure-web sure-worker
```

## Security

1. **HTTPS only**: Force via Traefik
2. **Strong passwords**: Database and user passwords
3. **API keys**: Securely store OpenAI API key
4. **Regular updates**: Keep Sure updated
5. **Access control**: Use Authelia groups

## Integration with Authelia

### Wife Group Access
Configure Authelia to allow wife access to Sure:

```yaml
# services/auth/configuration.yml
access_control:
  rules:
    - domain: "sure.yourdomain.com"
      policy: one_factor
      subject: "group:wife"
```

### User Setup
1. Create wife user in Authelia
2. Create corresponding user in Sure
3. Set appropriate permissions in Sure

## Troubleshooting Common Errors

### "ActiveRecord::ConnectionNotEstablished"
- Check database container
- Verify database credentials
- Check network connectivity
- Review database logs

### "OpenAI API Error"
- Verify API key is valid
- Check OpenAI account limits
- Review API usage
- Check Sure logs

### "Migration Failed"
- Check database migrations
- Verify database schema
- Check for conflicting data
- Review Rails logs

## Monitoring

Set up Grafana alerts for:
- Sure container not running
- Database connection failures
- High error rates in logs
- Disk space low in storage directory
