// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveStatusWidget.generated.h"

class UBorder;
class UHorizontalBox;
class USizeBox;
class UTextBlock;

/**
 * Top-of-screen Objective Assault status: round and clock, active objective,
 * capture progress and captures. Builds its own widget tree in C++ so it needs
 * no asset; reads only replicated director/objective state through
 * FSSObjectiveHudModel. Display only: it changes nothing.
 */
UCLASS()
class SSOBJUI_API USSObjectiveStatusWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;

	void SetDirector(ASSObjectiveAssaultDirector* InDirector) { Director = InDirector; }

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	TWeakObjectPtr<ASSObjectiveAssaultDirector> Director;

	struct FChipWidgets
	{
		UBorder* Outline = nullptr;
		UBorder* Fill = nullptr;
		UTextBlock* Letter = nullptr;
	};
	// Owned by WidgetTree (UPROPERTY there keeps them alive); raw pointers here.
	TArray<FChipWidgets> Chips;

	UPROPERTY(Transient) TObjectPtr<UTextBlock> RoundText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PhaseText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClockText;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> ObjectiveRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ObjectiveNameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;
	/** Section Assault: players alive, right of the status ("5 V 4"). */
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AliveText;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> StatusRow;
	UPROPERTY(Transient) TObjectPtr<USizeBox> BarSizeBox;
	UPROPERTY(Transient) TObjectPtr<UBorder> BarFill;
	UPROPERTY(Transient) TObjectPtr<UBorder> BarRest;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FirstSideText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FirstScoreText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SecondScoreText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SecondSideText;

	class UHorizontalBoxSlot* BarFillSlot = nullptr;
	class UHorizontalBoxSlot* BarRestSlot = nullptr;
};
