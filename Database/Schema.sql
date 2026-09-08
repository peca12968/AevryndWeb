USE Aevrynd;
GO

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
GO

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
GO
