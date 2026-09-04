/* Aevrynd 網站資料庫初始結構；敏感值只保存雜湊，不保存明文。 */
IF DB_ID(N'Aevrynd') IS NULL
    CREATE DATABASE [Aevrynd];
GO

USE [Aevrynd];
GO

IF OBJECT_ID(N'dbo.PortalUsers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.PortalUsers
    (
        UserId uniqueidentifier NOT NULL CONSTRAINT PK_PortalUsers PRIMARY KEY,
        Email nvarchar(320) NOT NULL CONSTRAINT UQ_PortalUsers_Email UNIQUE,
        IsEnabled bit NOT NULL CONSTRAINT DF_PortalUsers_IsEnabled DEFAULT (1),
        CreatedUtc datetimeoffset(3) NOT NULL CONSTRAINT DF_PortalUsers_CreatedUtc DEFAULT (sysdatetimeoffset())
    );
END;
GO

IF COL_LENGTH(N'dbo.PortalUsers', N'Role') IS NULL
    ALTER TABLE dbo.PortalUsers ADD Role varchar(16) NOT NULL CONSTRAINT DF_PortalUsers_Role DEFAULT ('User');
GO

/* 僅允許這五個已核准信箱登入；角色不包含任何密碼或 OTP 秘密。 */
MERGE dbo.PortalUsers AS target
USING (VALUES
    (CONVERT(uniqueidentifier, '8d4b51f5-9bf2-4d5a-9d9c-6b8b5f6e0001'), N'slime12968@gmail.com', 'Admin'),
    (CONVERT(uniqueidentifier, '8d4b51f5-9bf2-4d5a-9d9c-6b8b5f6e0002'), N'peca12968@gmail.com', 'Admin'),
    (CONVERT(uniqueidentifier, '8d4b51f5-9bf2-4d5a-9d9c-6b8b5f6e0003'), N'en531@livemail.tw', 'User'),
    (CONVERT(uniqueidentifier, '8d4b51f5-9bf2-4d5a-9d9c-6b8b5f6e0004'), N'tokkinjoey@gmail.com', 'User'),
    (CONVERT(uniqueidentifier, '8d4b51f5-9bf2-4d5a-9d9c-6b8b5f6e0005'), N'geminjjj@gmail.com', 'User')
) AS source(UserId, Email, Role) ON target.Email = source.Email
WHEN MATCHED THEN UPDATE SET target.Role = source.Role, target.IsEnabled = 1
WHEN NOT MATCHED THEN INSERT (UserId, Email, Role, IsEnabled) VALUES (source.UserId, source.Email, source.Role, 1);
GO

IF OBJECT_ID(N'dbo.OtpChallenges', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.OtpChallenges
    (
        ChallengeId uniqueidentifier NOT NULL CONSTRAINT PK_OtpChallenges PRIMARY KEY,
        UserId uniqueidentifier NULL CONSTRAINT FK_OtpChallenges_PortalUsers REFERENCES dbo.PortalUsers(UserId),
        Email nvarchar(320) NOT NULL,
        CodeHash varbinary(64) NOT NULL,
        ExpiresUtc datetimeoffset(3) NOT NULL,
        Attempts tinyint NOT NULL CONSTRAINT DF_OtpChallenges_Attempts DEFAULT (0),
        ConsumedUtc datetimeoffset(3) NULL,
        CreatedUtc datetimeoffset(3) NOT NULL CONSTRAINT DF_OtpChallenges_CreatedUtc DEFAULT (sysdatetimeoffset())
    );
    CREATE INDEX IX_OtpChallenges_Email_ExpiresUtc ON dbo.OtpChallenges(Email, ExpiresUtc);
END;
GO

IF OBJECT_ID(N'dbo.PortalSessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.PortalSessions
    (
        SessionId nvarchar(128) NOT NULL CONSTRAINT PK_PortalSessions PRIMARY KEY,
        UserId uniqueidentifier NULL CONSTRAINT FK_PortalSessions_PortalUsers REFERENCES dbo.PortalUsers(UserId),
        SecurityStampHash varbinary(64) NOT NULL,
        AuthenticatedUtc datetimeoffset(3) NOT NULL,
        ExpiresUtc datetimeoffset(3) NOT NULL,
        RevokedUtc datetimeoffset(3) NULL
    );
    CREATE INDEX IX_PortalSessions_ExpiresUtc ON dbo.PortalSessions(ExpiresUtc);
END;
GO

IF OBJECT_ID(N'dbo.RemoteControlGrants', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.RemoteControlGrants
    (
        GrantId uniqueidentifier NOT NULL CONSTRAINT PK_RemoteControlGrants PRIMARY KEY,
        SessionId nvarchar(128) NOT NULL CONSTRAINT FK_RemoteControlGrants_Sessions REFERENCES dbo.PortalSessions(SessionId),
        CapabilityMask int NOT NULL,
        PairingNonceHash varbinary(64) NOT NULL,
        EnabledUntilUtc datetimeoffset(3) NOT NULL,
        RevokedUtc datetimeoffset(3) NULL,
        CreatedUtc datetimeoffset(3) NOT NULL CONSTRAINT DF_RemoteControlGrants_CreatedUtc DEFAULT (sysdatetimeoffset())
    );
    CREATE INDEX IX_RemoteControlGrants_Session_EnabledUntilUtc ON dbo.RemoteControlGrants(SessionId, EnabledUntilUtc);
END;
GO

IF OBJECT_ID(N'dbo.OperationsNodes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.OperationsNodes
    (
        NodeId varchar(32) NOT NULL CONSTRAINT PK_OperationsNodes PRIMARY KEY,
        DisplayName nvarchar(80) NOT NULL,
        CpuPercent decimal(5,2) NULL,
        RamPercent decimal(5,2) NULL,
        GpuPercent decimal(5,2) NULL,
        SampledUtc datetimeoffset(3) NOT NULL,
        IsTrusted bit NOT NULL CONSTRAINT DF_OperationsNodes_IsTrusted DEFAULT (0),
        CONSTRAINT CK_OperationsNodes_Metrics CHECK
            ((CpuPercent IS NULL OR CpuPercent BETWEEN 0 AND 100) AND
             (RamPercent IS NULL OR RamPercent BETWEEN 0 AND 100) AND
             (GpuPercent IS NULL OR GpuPercent BETWEEN 0 AND 100))
    );
END;
GO

IF OBJECT_ID(N'dbo.OperationsWorkItems', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.OperationsWorkItems
    (
        WorkItemId uniqueidentifier NOT NULL CONSTRAINT PK_OperationsWorkItems PRIMARY KEY,
        Name nvarchar(160) NOT NULL,
        WorkType varchar(40) NOT NULL,
        NodeId varchar(32) NOT NULL CONSTRAINT FK_OperationsWorkItems_Nodes REFERENCES dbo.OperationsNodes(NodeId),
        StartedUtc datetimeoffset(3) NOT NULL,
        UpdatedUtc datetimeoffset(3) NULL,
        EndedUtc datetimeoffset(3) NULL,
        Status varchar(16) NOT NULL,
        EvidenceSummary nvarchar(240) NULL,
        Source varchar(32) NOT NULL CONSTRAINT DF_OperationsWorkItems_Source DEFAULT ('system'),
        CONSTRAINT CK_OperationsWorkItems_Status CHECK (Status IN ('working','completed','failed','blocked','cancelled')),
        CONSTRAINT CK_OperationsWorkItems_Timeline CHECK
            ((UpdatedUtc IS NULL OR UpdatedUtc >= StartedUtc) AND
             (EndedUtc IS NULL OR EndedUtc >= StartedUtc))
    );
    CREATE INDEX IX_OperationsWorkItems_UpdatedUtc ON dbo.OperationsWorkItems(UpdatedUtc DESC);
END;
GO

IF OBJECT_ID(N'dbo.AuditEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AuditEvents
    (
        AuditEventId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_AuditEvents PRIMARY KEY,
        EventType varchar(48) NOT NULL,
        Subject nvarchar(160) NOT NULL,
        Result varchar(16) NOT NULL,
        OccurredUtc datetimeoffset(3) NOT NULL CONSTRAINT DF_AuditEvents_OccurredUtc DEFAULT (sysdatetimeoffset()),
        EvidenceSummary nvarchar(240) NULL,
        CONSTRAINT CK_AuditEvents_Result CHECK (Result IN ('started','completed','failed','blocked','cancelled'))
    );
    CREATE INDEX IX_AuditEvents_OccurredUtc ON dbo.AuditEvents(OccurredUtc DESC);
END;
GO
