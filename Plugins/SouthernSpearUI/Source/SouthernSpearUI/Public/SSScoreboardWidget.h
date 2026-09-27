// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSScoreboardWidget.generated.h"

class UBorder;
class UTextBlock;

/**
 * Scoreboard (hold Tab): the viewer's own side first as 3 ACR, the other side
 * as MAF (viewer-relative, like every Southern Spear presentation), each
 * player's eliminations, deaths, assists and ping. Reads USSScoreboardState
 * (Core), which the Lyra bridge fills. Built in C++ in the website style.
 */
UCLASS()
class SSUI_API USSScoreboardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	static constexpr int32 RowsPerSide = 10;

private:
	struct FRowWidgets
	{
		UBorder* Plate = nullptr;
		UTextBlock* Name = nullptr;
		UTextBlock* Kills = nullptr;
		UTextBlock* Deaths = nullptr;
		UTextBlock* Assists = nullptr;
		UTextBlock* Ping = nullptr;
	};
	void Refresh();

	TArray<FRowWidgets> Sides[2];
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> Totals;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Keep; // row widgets, owned by the tree
	float RefreshIn = 0.f;
	float Elapsed = 0.f;
	UPROPERTY(Transient) TObjectPtr<UWidget> Panel;
};
