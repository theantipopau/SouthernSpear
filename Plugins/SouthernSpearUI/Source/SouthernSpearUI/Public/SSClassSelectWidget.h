// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSKitSelection.h"
#include "SSClassSelectWidget.generated.h"

class AActor;
class ASceneCapture2D;
class UBorder;
class UImage;
class UTextureRenderTarget2D;
class UTextBlock;
class UWidget;

/**
 * Class selection (on first deployment and after death): Rifleman, Medic,
 * Machine Gunner, Sniper, Grenadier, with the kit each carries (standard or
 * Special Forces, from USSKitSelection). Picking one writes the request to
 * USSKitSelection; the Lyra bridge grants it (swapping the kit in place when
 * alive). Built in C++ in the Southern Spear style. Classes are listed down the left; the right
 * shows the selected soldier and weapon in 3D as they appear in game (the friendly look, a
 * turntable scene capture of a stage spawned high above the map while the screen is open).
 * Clicking a class selects it; DEPLOY confirms.
 */
UCLASS()
class SSUI_API USSClassSelectWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Opens the screen (UI input, cursor). bAfterDeath changes the heading. */
	void Open(bool bAfterDeath);
	void Close();

private:
	UFUNCTION() void OnRifleman();
	UFUNCTION() void OnMedic();
	UFUNCTION() void OnMachineGunner();
	UFUNCTION() void OnSniper();
	UFUNCTION() void OnGrenadier();
	UFUNCTION() void OnDeploy();
	void Select(int32 Index);
	void Pick(ESSKitRole Role);
	void Refresh();
	void BuildStage();
	void DestroyStage();
	void ShowWeapon(int32 Index);

	UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Kicker;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> WeaponTexts;
	UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> CardEdges;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Cards;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PreviewName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PreviewWeapon;
	UPROPERTY(Transient) TObjectPtr<UImage> PreviewImage;
	UPROPERTY(Transient) TObjectPtr<UWidget> PreviewPanel;
	UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> PreviewTarget;
	UPROPERTY(Transient) TObjectPtr<AActor> Stage;
	UPROPERTY(Transient) TObjectPtr<AActor> StageSoldier;
	UPROPERTY(Transient) TObjectPtr<AActor> StageWeapon;
	UPROPERTY(Transient) TObjectPtr<ASceneCapture2D> StageCamera;
	UPROPERTY(Transient) TObjectPtr<class USkeletalMeshComponent> StageBody;
	bool bStageLocalityApplied = false;
	float StageBodyYaw = -90.f;
	int32 Selected = 0;
	float Elapsed = 0.f;
};
