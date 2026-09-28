// Copyright Southern Spear. All Rights Reserved.
//
// Headless pre-dedicated-server smoke test for real player connections and
// server authority. UE's in-process network test worlds provide the server and
// clients; this does not replace packaged dedicated-server acceptance.

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Engine/NetDriver.h"
#include "Engine/World.h"
#include "GameMapsSettings.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Misc/AutomationTest.h"
#include "Tests/NetTestHelpers.h"

namespace
{
	constexpr EAutomationTestFlags SSGameplayAuthoritySmokeFlags =
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter;

	/** Temporarily removes project startup behavior while headless clients connect. */
	class FScopedTestStartupSettings
	{
	public:
		FScopedTestStartupSettings(const FString& TestMap, const FString& TestGameMode)
			: OriginalMap(UGameMapsSettings::GetGameDefaultMap())
			, OriginalGameMode(UGameMapsSettings::GetGlobalDefaultGameMode())
		{
			UGameMapsSettings::SetGameDefaultMap(TestMap);
			UGameMapsSettings::SetGlobalDefaultGameMode(TestGameMode);
		}

		~FScopedTestStartupSettings()
		{
			UGameMapsSettings::SetGameDefaultMap(OriginalMap);
			UGameMapsSettings::SetGlobalDefaultGameMode(OriginalGameMode);
		}

	private:
		FString OriginalMap;
		FString OriginalGameMode;
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FSSGameplayTwoPlayerAuthoritySmoke,
	"SouthernSpear.Network.Gameplay.TwoPlayerAuthoritySmoke",
	SSGameplayAuthoritySmokeFlags)

bool FSSGameplayTwoPlayerAuthoritySmoke::RunTest(const FString& Parameters)
{
	// TestWorlds is editor-only. Its PIE settings intentionally make this an
	// in-process dedicated-mode server with loopback clients, without needing a
	// server target or packaged server process. This is not DS acceptance.
	UE::Net::FTestWorlds TestWorlds;
	UWorld* ServerWorld = TestWorlds.Server.GetWorld();
	if (!TestNotNull(TEXT("network test server world exists"), ServerWorld))
	{
		return false;
	}
	if (!TestTrue(TEXT("network test server world loaded"), TestWorlds.Server.IsLoaded()))
	{
		return false;
	}
	UNetDriver* ServerNetDriver = TestWorlds.Server.GetNetDriver();
	if (!TestNotNull(TEXT("server has a network driver"), ServerNetDriver))
	{
		return false;
	}
	TestTrue(TEXT("server network driver is authoritative"), ServerNetDriver->IsServer());

	AGameModeBase* GameMode = ServerWorld->GetAuthGameMode();
	if (!TestNotNull(TEXT("test server GameMode initialized"), GameMode))
	{
		return false;
	}
	TestTrue(TEXT("test server uses the neutral engine GameMode fixture"),
		GameMode->GetClass()->GetPathName() == TEXT("/Script/Engine.GameMode"));

	TestEqual(TEXT("test server runs in dedicated-server mode, not standalone"),
		ServerWorld->GetNetMode(), NM_DedicatedServer);

	{
		// The helper boots each client on GameDefaultMap before it travels to the
		// server. Southern Spear's default is an interactive front end whose
		// PostLogin adds widgets to a real viewport, which a headless test lacks.
		// Start clients on Engine's empty Entry map with Engine's neutral GameMode,
		// then restore project defaults as soon as both clients have connected.
		FScopedTestStartupSettings TestStartup(TEXT("/Engine/Maps/Entry"), TEXT("/Script/Engine.GameMode"));
		if (!TestTrue(TEXT("first player connects"), TestWorlds.CreateAndConnectClient()))
		{
			return false;
		}
		if (!TestTrue(TEXT("second player connects"), TestWorlds.ConnectNewClient() != INDEX_NONE))
		{
			return false;
		}
	}

	const double ServerTimeBeforeTicks = ServerWorld->GetTimeSeconds();
	TestWorlds.TickAll(5);
	TestTrue(TEXT("server world advanced through five ticks"),
		ServerWorld->GetTimeSeconds() > ServerTimeBeforeTicks);
	TestEqual(TEXT("two network clients connected"), TestWorlds.Clients.Num(), 2);
	TestEqual(TEXT("server GameMode recognizes two players"), GameMode->GetNumPlayers(), 2);

	// The connection harness supplies networked controllers. Spawn the two
	// player-controlled pawns through the authoritative GameMode before the
	// second tick window so we check gameplay actors as well as the connections.
	int32 PlayerIndex = 0;
	for (FConstPlayerControllerIterator It = ServerWorld->GetPlayerControllerIterator(); It; ++It)
	{
		if (APlayerController* PlayerController = It->Get())
		{
			if (!PlayerController->GetPawn())
			{
				const FVector SpawnLocation(500.f * PlayerIndex, 0.f, 100.f);
				GameMode->RestartPlayerAtTransform(PlayerController,
					FTransform(FRotator::ZeroRotator, SpawnLocation));
			}
			++PlayerIndex;
		}
	}
	TestWorlds.TickAll(5);

	TArray<APlayerController*> MatchedServerPlayers;
	TArray<APawn*> MatchedServerPawns;
	for (uint32 ClientIndex = 0; ClientIndex < static_cast<uint32>(TestWorlds.Clients.Num()); ++ClientIndex)
	{
		UWorld* ClientWorld = TestWorlds.Clients[ClientIndex].GetWorld();
		if (!TestNotNull(TEXT("client world exists"), ClientWorld))
		{
			return false;
		}

		APlayerController* ClientPlayer = ClientWorld->GetFirstPlayerController();
		APlayerController* ServerPlayer = TestWorlds.GetServerPlayerControllerOfClient(ClientIndex);
		if (!TestNotNull(TEXT("client player controller exists"), ClientPlayer)
			|| !TestNotNull(TEXT("matching server player controller exists"), ServerPlayer))
		{
			return false;
		}

		TestEqual(TEXT("client world is non-authoritative"), ClientWorld->GetNetMode(), NM_Client);
		TestFalse(TEXT("client player controller is not authoritative"), ClientPlayer->HasAuthority());
		TestEqual(TEXT("client player controller is autonomous"), ClientPlayer->GetLocalRole(), ROLE_AutonomousProxy);

		TestTrue(TEXT("server player controller has authority after ticking"), ServerPlayer->HasAuthority());
		TestEqual(TEXT("server player controller has the authority role"), ServerPlayer->GetLocalRole(), ROLE_Authority);
		if (!TestNotNull(TEXT("server player has a PlayerState"), ServerPlayer->PlayerState.Get())
			|| !TestNotNull(TEXT("server player has a possessed pawn"), ServerPlayer->GetPawn().Get()))
		{
			return false;
		}
		APawn* ServerPawn = ServerPlayer->GetPawn();
		TestTrue(TEXT("server player pawn has authority"), ServerPawn->HasAuthority());
		TestFalse(TEXT("each client maps to a distinct server pawn"), MatchedServerPawns.Contains(ServerPawn));
		MatchedServerPawns.Add(ServerPawn);

		TestNotNull(TEXT("client player has a PlayerState"), ClientPlayer->PlayerState.Get());
		APawn* ClientPawn = ClientPlayer->GetPawn();
		if (TestNotNull(TEXT("client player has its pawn"), ClientPawn))
		{
			TestFalse(TEXT("client pawn is not authoritative"), ClientPawn->HasAuthority());
			TestEqual(TEXT("client pawn has the autonomous role"), ClientPawn->GetLocalRole(), ROLE_AutonomousProxy);
		}
		TestFalse(TEXT("each client maps to a distinct server player"), MatchedServerPlayers.Contains(ServerPlayer));
		MatchedServerPlayers.Add(ServerPlayer);
	}

	TestEqual(TEXT("two distinct server-side players were matched"), MatchedServerPlayers.Num(), 2);
	TestEqual(TEXT("two distinct authoritative server pawns were matched"), MatchedServerPawns.Num(), 2);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR
