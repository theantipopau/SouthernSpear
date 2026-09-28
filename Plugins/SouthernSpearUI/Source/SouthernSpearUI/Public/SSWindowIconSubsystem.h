// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/EngineSubsystem.h"
#include "SSWindowIconSubsystem.generated.h"

/**
 * Game window and taskbar icon. A packaged SouthernSpear.exe embeds Build/Windows/Application.ico, but
 * development runs launch UnrealEditor.exe -game, whose embedded icon is Unreal's. When the project
 * icon file exists (development), it is set on the game window as soon as the window exists (Windows only;
 * never in the editor).
 */
UCLASS()
class USSWindowIconSubsystem : public UEngineSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	bool TryApply(float DeltaTime);

	FTSTicker::FDelegateHandle TickHandle;
	float Waited = 0.f;
	bool bApplied = false;
};
