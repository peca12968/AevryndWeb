using System.Data;
using AevryndWeb.Models;
using Microsoft.Data.SqlClient;

namespace AevryndWeb.Data;

public interface ISiteStatisticsStore
{
    Task InitializeAsync(CancellationToken cancellationToken = default);
    Task<SiteStatisticsResponse> ReadAsync(CancellationToken cancellationToken = default);
    Task<SiteStatisticsResponse> HeartbeatAsync(Guid sessionId, Guid? viewId, CancellationToken cancellationToken = default);
}

public sealed class SqlSiteStatisticsStore(IConfiguration configuration) : ISiteStatisticsStore
{
    private static readonly TimeSpan OnlineWindow = TimeSpan.FromSeconds(70);
    private static readonly TimeSpan SessionRetention = TimeSpan.FromDays(1);
    private readonly string _connectionString = configuration.GetConnectionString("Aevrynd")
        ?? throw new InvalidOperationException("ConnectionStrings:Aevrynd is required.");

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        var target = new SqlConnectionStringBuilder(_connectionString);
        if (!string.Equals(target.InitialCatalog, "Aevrynd", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("The site must use the existing Aevrynd database.");
        }

        await using var targetConnection = new SqlConnection(_connectionString);
        await targetConnection.OpenAsync(cancellationToken);
        await using var schema = targetConnection.CreateCommand();
        schema.CommandText = """
            IF OBJECT_ID(N'dbo.SiteOnlineSessions', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.SiteOnlineSessions
                (
                    SessionId uniqueidentifier NOT NULL CONSTRAINT PK_SiteOnlineSessions PRIMARY KEY,
                    LastSeenUtc datetime2(3) NOT NULL
                );
                CREATE INDEX IX_SiteOnlineSessions_LastSeenUtc
                    ON dbo.SiteOnlineSessions (LastSeenUtc);
            END;

            IF OBJECT_ID(N'dbo.SitePageViews', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.SitePageViews
                (
                    ViewId uniqueidentifier NOT NULL CONSTRAINT PK_SitePageViews PRIMARY KEY,
                    SessionId uniqueidentifier NOT NULL,
                    ViewedAtUtc datetime2(3) NOT NULL
                );
                CREATE INDEX IX_SitePageViews_ViewedAtUtc
                    ON dbo.SitePageViews (ViewedAtUtc);
            END;
            """;
        await schema.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task<SiteStatisticsResponse> ReadAsync(CancellationToken cancellationToken = default)
    {
        var now = DateTime.UtcNow;
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT
                (SELECT COUNT_BIG(*) FROM dbo.SiteOnlineSessions WHERE LastSeenUtc >= @onlineCutoff),
                (SELECT COUNT_BIG(*) FROM dbo.SitePageViews);
            """;
        command.Parameters.Add(new SqlParameter("@onlineCutoff", SqlDbType.DateTime2) { Value = now - OnlineWindow });
        return await ReadResultAsync(command, cancellationToken);
    }

    public async Task<SiteStatisticsResponse> HeartbeatAsync(
        Guid sessionId,
        Guid? viewId,
        CancellationToken cancellationToken = default)
    {
        var now = DateTime.UtcNow;
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var transaction = await connection.BeginTransactionAsync(IsolationLevel.Serializable, cancellationToken);
        await using var command = connection.CreateCommand();
        command.Transaction = (SqlTransaction)transaction;
        command.CommandText = """
            UPDATE dbo.SiteOnlineSessions WITH (UPDLOCK, SERIALIZABLE)
            SET LastSeenUtc = @now
            WHERE SessionId = @sessionId;

            IF @@ROWCOUNT = 0
                INSERT dbo.SiteOnlineSessions (SessionId, LastSeenUtc) VALUES (@sessionId, @now);

            IF @viewId IS NOT NULL AND NOT EXISTS
                (SELECT 1 FROM dbo.SitePageViews WITH (UPDLOCK, SERIALIZABLE) WHERE ViewId = @viewId)
                INSERT dbo.SitePageViews (ViewId, SessionId, ViewedAtUtc) VALUES (@viewId, @sessionId, @now);

            DELETE dbo.SiteOnlineSessions WHERE LastSeenUtc < @retentionCutoff;

            SELECT
                (SELECT COUNT_BIG(*) FROM dbo.SiteOnlineSessions WHERE LastSeenUtc >= @onlineCutoff),
                (SELECT COUNT_BIG(*) FROM dbo.SitePageViews);
            """;
        command.Parameters.Add(new SqlParameter("@sessionId", SqlDbType.UniqueIdentifier) { Value = sessionId });
        command.Parameters.Add(new SqlParameter("@viewId", SqlDbType.UniqueIdentifier) { Value = viewId ?? (object)DBNull.Value });
        command.Parameters.Add(new SqlParameter("@now", SqlDbType.DateTime2) { Value = now });
        command.Parameters.Add(new SqlParameter("@onlineCutoff", SqlDbType.DateTime2) { Value = now - OnlineWindow });
        command.Parameters.Add(new SqlParameter("@retentionCutoff", SqlDbType.DateTime2) { Value = now - SessionRetention });

        var result = await ReadResultAsync(command, cancellationToken);
        await transaction.CommitAsync(cancellationToken);
        return result;
    }

    private static async Task<SiteStatisticsResponse> ReadResultAsync(
        SqlCommand command,
        CancellationToken cancellationToken)
    {
        await using var reader = await command.ExecuteReaderAsync(CommandBehavior.SingleRow, cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            throw new DataException("The statistics query returned no result.");
        }

        return new SiteStatisticsResponse(reader.GetInt64(0), reader.GetInt64(1));
    }
}
